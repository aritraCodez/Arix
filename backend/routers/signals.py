"""
Signal endpoint router.
Provides the /signal endpoint for fetching trading signals.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from config import get_settings
from services.data_fetcher import AssetType, fetch_ohlcv
from services.indicators import compute_all_indicators
from services.signal_engine import RiskLevel, generate_signal
from services.ml_predictor import get_predictor
from services.ai_analyst import get_ai_analyst
from utils.cache import cache
from utils.locks import lock_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/signal")
async def get_signal(
    symbol: str = Query(..., description="Asset symbol (e.g., BTCUSDT, EURUSD, AAPL, GOLD)"),
    type: AssetType = Query(..., description="Asset type: crypto, forex, stock, commodity"),
    risk: RiskLevel = Query(RiskLevel.MEDIUM, description="Risk level: low, medium, high"),
    use_ml: bool = Query(True, description="Whether to include ML predictions in the signal"),
    use_ai: bool = Query(True, description="Whether to include Gemini AI analysis in the signal"),
    use_ai_model: str = Query(None, description="Override Gemini model (e.g., gemini-2.5-pro)"),
):
    """
    Get trading signal for the given asset.
    
    Fetches real-time OHLC data, computes technical indicators (RSI, MACD, EMA),
    optionally runs ML prediction and AI analysis, and returns a weighted signal.
    
    Response includes:
    - signal: UP / DOWN / NO_TRADE
    - confidence: 0–100%
    - indicators: RSI, MACD, EMA trend details
    - ml_prediction: LSTM probability (if enabled)
    - ai_analysis: Gemini AI score + reasoning (if enabled)
    - timestamp: ISO format
    """
    start_time = datetime.now(timezone.utc)
    settings = get_settings()

    # Build cache key
    cache_key = f"signal:{symbol.upper()}:{type.value}:{risk.value}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for {cache_key}")
        return cached

    # Acquire per-symbol lock to prevent duplicate fetches
    lock = await lock_manager.acquire(f"fetch:{symbol.upper()}")

    async with lock:
        # Double-check cache after acquiring lock (another request may have filled it)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit (post-lock) for {cache_key}")
            return cached

        try:
            # 1. Fetch OHLCV data
            df = await fetch_ohlcv(
                symbol=symbol.upper(),
                asset_type=type,
                interval="1m",
                limit=100,
            )

            if len(df) < 35:
                raise HTTPException(
                    status_code=422,
                    detail=f"Insufficient market data for {symbol}. Got {len(df)} candles, need at least 35.",
                )

            # 2, 3, 4. Compute indicators, ML, and AI in parallel for speed
            async def run_ml():
                if use_ml:
                    predictor = get_predictor()
                    if predictor and predictor.enabled:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, lambda: predictor.predict(df))
                return None

            async def run_ai(indicator_results):
                if use_ai:
                    analyst = get_ai_analyst()
                    if analyst and analyst.is_session_active():
                        indicators_dict = indicator_results.to_dict()
                        prices = indicator_results.raw_prices or []
                        return await analyst.analyze(
                            symbol=symbol.upper(),
                            indicators=indicators_dict,
                            prices=prices,
                            model_override=use_ai_model,
                        )
                return None

            # First compute indicators (needed for AI prompt)
            indicators = await asyncio.to_thread(compute_all_indicators, df["close"])

            # Then run ML and AI in parallel
            ml_probability, ai_result = await asyncio.gather(
                run_ml(),
                run_ai(indicators),
            )

            # 5. Generate signal
            now = datetime.now(timezone.utc).isoformat()
            result = generate_signal(
                indicators=indicators,
                risk_level=risk,
                ml_probability=ml_probability,
                ai_result=ai_result,
                symbol=symbol.upper(),
                asset_type=type.value,
                timestamp=now,
            )

            response = result.to_dict()
            
            # Add execution time in ms
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response["execution_time"] = round(execution_time, 2)

            # 6. Cache the result
            ttl = settings.CACHE_TTL_CRYPTO if type == AssetType.CRYPTO else settings.CACHE_TTL_OTHER
            cache.set(cache_key, response, ttl=ttl)

            return response

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate signal for {symbol}: {str(e)}",
            )
