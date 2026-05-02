"""
AI Analyst service.
Uses Google Gemini to provide AI-powered market analysis.
Falls back gracefully if API key is missing or Gemini is unavailable.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try importing google-genai
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed — AI analysis disabled")


# System prompt for Gemini
SYSTEM_PROMPT = """You are a professional quantitative trading analyst. You analyze technical indicators and price data to determine short-term (1-5 minute) price direction for trading signals.

You will receive market data including:
- RSI (14-period)
- MACD (12, 26, 9)
- EMA trend (9/21)
- Bollinger Bands (20, 2)
- Recent close prices

Analyze the data and respond with ONLY a valid JSON object (no markdown, no code fences):
{
  "direction": "UP" or "DOWN",
  "score": <float from -1.0 to 1.0, negative=bearish, positive=bullish>,
  "confidence": <int from 0 to 100>,
  "reasoning": "<1-2 sentence explanation of your analysis>"
}

Rules:
- Be decisive. Always pick UP or DOWN.
- Score magnitude reflects conviction: 0.1 = weak, 0.5 = moderate, 1.0 = very strong.
- Confidence reflects how reliable you think the signal is.
- Focus on confluence of indicators. Multiple indicators agreeing = higher confidence.
- Consider momentum and trend alignment.
- Keep reasoning concise and actionable."""


class AIAnalyst:
    """
    Manages Gemini AI analysis with session timer and per-symbol caching.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-2.0-flash",
        enabled: bool = False,
        analysis_ttl: int = 30,
        session_minutes: int = 0,
    ):
        self.api_key = api_key
        self.model = model
        self.enabled = enabled and GENAI_AVAILABLE and bool(api_key)
        self.analysis_ttl = analysis_ttl
        self.session_minutes = session_minutes  # 0 = unlimited
        self.session_start: Optional[datetime] = None
        self._cache: Dict[str, Dict[str, Any]] = {}  # symbol -> {result, timestamp}
        self.client = None

        if self.enabled:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize the Gemini client."""
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini AI client initialized (model={self.model})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
            self.enabled = False

    def is_session_active(self) -> bool:
        """Check if the AI session is still active (considering timer)."""
        if not self.enabled:
            return False
        if self.session_minutes == 0:  # unlimited
            return True
        if self.session_start is None:
            return True  # session not started yet, will start on first call
        elapsed = (datetime.now(timezone.utc) - self.session_start).total_seconds() / 60
        if elapsed >= self.session_minutes:
            logger.info(f"AI session expired after {self.session_minutes} minutes")
            self.enabled = False
            return False
        return True

    def get_session_remaining(self) -> Optional[str]:
        """Get remaining session time as 'MM:SS' string, or None if unlimited."""
        if self.session_minutes == 0:
            return None  # unlimited
        if self.session_start is None:
            return f"{self.session_minutes}:00"
        elapsed = (datetime.now(timezone.utc) - self.session_start).total_seconds()
        remaining = max(0, (self.session_minutes * 60) - elapsed)
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        return f"{minutes}:{seconds:02d}"

    def start_session(self) -> None:
        """Manually start or restart the AI session."""
        if not GENAI_AVAILABLE or not self.api_key:
            logger.warning("Cannot start AI session — missing dependencies or API key")
            return
        self.enabled = True
        self.session_start = datetime.now(timezone.utc)
        self._cache.clear()
        if not self.client:
            self._init_client()
        logger.info(
            f"AI session started (model={self.model}, "
            f"duration={'unlimited' if self.session_minutes == 0 else f'{self.session_minutes}min'})"
        )

    def stop_session(self) -> None:
        """Manually stop the AI session."""
        self.enabled = False
        self.session_start = None
        self._cache.clear()
        logger.info("AI session stopped")

    def _get_cached(self, symbol: str) -> Optional[Dict]:
        """Get cached analysis result if still valid."""
        if symbol in self._cache:
            entry = self._cache[symbol]
            age = time.time() - entry["timestamp"]
            if age < self.analysis_ttl:
                return entry["result"]
            else:
                del self._cache[symbol]
        return None

    def _set_cached(self, symbol: str, result: Dict) -> None:
        """Cache an analysis result."""
        self._cache[symbol] = {
            "result": result,
            "timestamp": time.time(),
        }

    def _build_prompt(self, symbol: str, indicators: dict, prices: list) -> str:
        """Build the analysis prompt with market data."""
        market_data = {
            "symbol": symbol,
            "rsi": {
                "value": indicators.get("rsi", {}).get("value"),
                "signal": indicators.get("rsi", {}).get("signal"),
            },
            "macd": {
                "histogram": indicators.get("macd", {}).get("histogram"),
                "signal": indicators.get("macd", {}).get("signal"),
            },
            "ema_trend": {
                "signal": indicators.get("ema_trend", {}).get("signal"),
                "short": indicators.get("ema_trend", {}).get("short"),
                "long": indicators.get("ema_trend", {}).get("long"),
            },
            "bollinger": indicators.get("bollinger", {}),
            "recent_closes": prices[-5:] if prices else [],
            "current_price": prices[-1] if prices else None,
        }

        return f"Analyze this market data and provide a trading signal:\n{json.dumps(market_data, indent=2)}"

    async def analyze(
        self,
        symbol: str,
        indicators: dict,
        prices: list,
        model_override: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Run Gemini AI analysis on the given market data.

        Args:
            symbol: Asset symbol
            indicators: Dict from IndicatorResults.to_dict()
            prices: List of recent close prices
            model_override: Override model for this request

        Returns:
            Dict with {score, reasoning, confidence, model} or None
        """
        if not self.is_session_active() or not self.client:
            return None

        # Start session timer on first call if not started
        if self.session_start is None and self.session_minutes > 0:
            self.session_start = datetime.now(timezone.utc)

        # Check cache
        cache_key = f"{symbol}:{model_override or self.model}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.debug(f"AI cache hit for {cache_key}")
            return cached

        model = model_override or self.model
        prompt = self._build_prompt(symbol, indicators, prices)

        try:
            import asyncio

            # Run Gemini call in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.3,
                        "max_output_tokens": 256,
                    },
                ),
            )

            # Parse the response
            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first line (```json) and last line (```)
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()

            result_data = json.loads(text)

            # Validate and clamp values
            score = max(-1.0, min(1.0, float(result_data.get("score", 0))))
            confidence = max(0, min(100, int(result_data.get("confidence", 50))))
            reasoning = str(result_data.get("reasoning", "No reasoning provided"))
            direction = result_data.get("direction", "UP" if score > 0 else "DOWN")

            result = {
                "score": score,
                "direction": direction,
                "confidence": confidence,
                "reasoning": reasoning,
                "model": model,
                "enabled": True,
                "session_remaining": self.get_session_remaining(),
            }

            self._set_cached(cache_key, result)
            logger.info(
                f"AI analysis for {symbol}: {direction} "
                f"(score={score:.2f}, confidence={confidence}%, model={model})"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"AI response parse error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"AI analysis failed for {symbol}: {e}")
            return None

    def get_status(self) -> Dict:
        """Get current AI analyst status."""
        return {
            "enabled": self.enabled,
            "available": GENAI_AVAILABLE and bool(self.api_key),
            "model": self.model,
            "session_minutes": self.session_minutes,
            "session_remaining": self.get_session_remaining() if self.enabled else None,
            "analysis_ttl": self.analysis_ttl,
            "cache_size": len(self._cache),
        }


# Global AI analyst instance (initialized in main.py startup)
ai_analyst: Optional[AIAnalyst] = None


def init_ai_analyst(
    api_key: str,
    model: str,
    enabled: bool,
    analysis_ttl: int,
    session_minutes: int,
) -> AIAnalyst:
    """Initialize the global AI analyst."""
    global ai_analyst
    ai_analyst = AIAnalyst(
        api_key=api_key,
        model=model,
        enabled=enabled,
        analysis_ttl=analysis_ttl,
        session_minutes=session_minutes,
    )
    return ai_analyst


def get_ai_analyst() -> Optional[AIAnalyst]:
    """Get the global AI analyst instance."""
    return ai_analyst
