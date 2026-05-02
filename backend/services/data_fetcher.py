"""
Data fetcher service.
Retrieves OHLCV candle data from Binance (crypto) and Yahoo Finance (forex/stocks/commodities).
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import httpx
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"
    COMMODITY = "commodity"


# Symbol mappings for Yahoo Finance
# Forex pairs need =X suffix, commodities use futures symbols
YAHOO_SYMBOL_MAP = {
    # Forex
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X",
    "CADJPY": "CADJPY=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "GBPCHF": "GBPCHF=X",
    "AUDCAD": "AUDCAD=X",
    "EURAUD": "EURAUD=X",
    "CHFJPY": "CHFJPY=X",
    "EURGBP": "EURGBP=X",
    "GBPNZD": "GBPNZD=X",
    "AUDNZD": "AUDNZD=X",
    "EURNZD": "EURNZD=X",
    "GBPCAD": "GBPCAD=X",
    "AUDJPY": "AUDJPY=X",
    "GBPAUD": "GBPAUD=X",
    "USDPHP": "USDPHP=X",
    "NZDJPY": "NZDJPY=X",
    # Commodities
    "GOLD": "GC=F", "XAUUSD": "GC=F", "SILVER": "SI=F",
    "OIL": "CL=F", "CRUDEOIL": "CL=F", "UKBRENT": "BZ=F", "NATGAS": "NG=F",
    # Stocks
    "FACEBOOK": "META", "META": "META", "APPLE": "AAPL", "GOOGLE": "GOOGL",
    "AMAZON": "AMZN", "NETFLIX": "NFLX", "TESLA": "TSLA", "MICROSOFT": "MSFT",
    "NVIDIA": "NVDA", "INTEL": "INTC", "ALIBABA": "BABA", "VISA": "V",
    # Indices
    "US100": "NQ=F", "US30": "YM=F", "US500": "ES=F", "GER40": "DAX",
    "UK100": "FTSE", "J225": "N225", "HK50": "HSI"
}

# Binance-supported crypto pairs
BINANCE_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "SHIBUSDT", "TRXUSDT", "ATOMUSDT",
}


async def fetch_binance_klines(
    symbol: str,
    interval: str = "1m",
    limit: int = 100,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Binance public API.
    No API key required.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Candle interval (1m, 5m, 15m, 1h, etc.)
        limit: Number of candles (max 1000)
    
    Returns:
        DataFrame with columns: open, high, low, close, volume, timestamp
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore",
    ])

    # Convert to numeric
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    
    # Keep only needed columns
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df = df.dropna()
    df = df.reset_index(drop=True)

    logger.info(f"Fetched {len(df)} candles from Binance for {symbol}")
    return df


def fetch_yahoo_data(
    symbol: str,
    asset_type: AssetType,
    interval: str = "1m",
    period: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.
    No API key required.
    
    Args:
        symbol: Raw symbol (e.g., "EURUSD", "AAPL", "GOLD")
        asset_type: Type of asset for symbol mapping
        interval: Candle interval (1m, 5m, 15m, 1h, 1d)
        period: Lookback period (1d, 5d, 1mo)
    
    Returns:
        DataFrame with columns: open, high, low, close, volume, timestamp
    """
    # 1. Map symbol to Yahoo Finance format
    symbol_upper = symbol.upper()
    yf_symbol = YAHOO_SYMBOL_MAP.get(symbol_upper)

    if not yf_symbol:
        if asset_type == AssetType.FOREX:
            # Forex pairs need =X (e.g., CADJPY -> CADJPY=X)
            yf_symbol = f"{symbol_upper}=X" if not symbol_upper.endswith("=X") else symbol_upper
        else:
            yf_symbol = symbol_upper

    logger.info(f"Fetching Yahoo Finance data: {yf_symbol} ({asset_type})")

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned from Yahoo Finance for {yf_symbol}")

    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]

    # Ensure we have the required columns
    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column '{col}' in Yahoo Finance data for {yf_symbol}")

    # Add timestamp column from index
    df["timestamp"] = df.index
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df = df.reset_index(drop=True)
    df = df.dropna()

    logger.info(f"Fetched {len(df)} candles from Yahoo Finance for {yf_symbol}")
    return df


async def fetch_ohlcv(
    symbol: str,
    asset_type: AssetType,
    interval: str = "1m",
    limit: int = 100,
) -> pd.DataFrame:
    """
    Unified data fetcher. Routes to appropriate data source
    based on asset type.
    
    Args:
        symbol: Asset symbol
        asset_type: Type of asset (crypto/forex/stock/commodity)
        interval: Candle interval
        limit: Number of candles
    
    Returns:
        OHLCV DataFrame
    
    Raises:
        ValueError: If no data available
        httpx.HTTPError: If API request fails
    """
    if asset_type == AssetType.CRYPTO:
        return await fetch_binance_klines(symbol, interval, limit)
    else:
        # Yahoo Finance uses period-based fetching
        # Map limit to appropriate period
        period_map = {
            "1m": "1d",    # 1-min candles: get 1 day of data
            "5m": "5d",    # 5-min candles: get 5 days
            "15m": "5d",   # 15-min candles: get 5 days
            "1h": "1mo",   # 1-hour candles: get 1 month
            "1d": "1y",    # Daily candles: get 1 year
        }
        period = period_map.get(interval, "1d")
        
        # yfinance is synchronous, run in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: fetch_yahoo_data(symbol, asset_type, interval, period)
        )
        
        # Trim to requested limit
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)
        
        return df
