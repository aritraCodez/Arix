"""
Pytest fixtures and test configuration.
Provides mock data, test client, and cache management.
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_ohlcv_uptrend() -> pd.DataFrame:
    """Generate a DataFrame simulating an uptrend (100 candles)."""
    np.random.seed(42)
    n = 100
    base_price = 100.0
    
    # Generate uptrending prices with noise
    trend = np.linspace(0, 10, n)
    noise = np.random.normal(0, 0.5, n)
    close = base_price + trend + noise
    
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC"),
        "open": close - np.random.uniform(0, 0.3, n),
        "high": close + np.random.uniform(0, 0.5, n),
        "low": close - np.random.uniform(0, 0.5, n),
        "close": close,
        "volume": np.random.uniform(1000, 5000, n),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_ohlcv_downtrend() -> pd.DataFrame:
    """Generate a DataFrame simulating a downtrend (100 candles)."""
    np.random.seed(42)
    n = 100
    base_price = 110.0
    
    # Generate downtrending prices
    trend = np.linspace(0, -10, n)
    noise = np.random.normal(0, 0.5, n)
    close = base_price + trend + noise
    
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC"),
        "open": close + np.random.uniform(0, 0.3, n),
        "high": close + np.random.uniform(0, 0.5, n),
        "low": close - np.random.uniform(0, 0.5, n),
        "close": close,
        "volume": np.random.uniform(1000, 5000, n),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_ohlcv_sideways() -> pd.DataFrame:
    """Generate a DataFrame simulating sideways/ranging market."""
    np.random.seed(42)
    n = 100
    base_price = 100.0
    
    noise = np.random.normal(0, 0.3, n)
    close = base_price + noise
    
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC"),
        "open": close - np.random.uniform(0, 0.1, n),
        "high": close + np.random.uniform(0, 0.2, n),
        "low": close - np.random.uniform(0, 0.2, n),
        "close": close,
        "volume": np.random.uniform(1000, 5000, n),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_close_prices(sample_ohlcv_uptrend) -> pd.Series:
    """Extract close prices from uptrend data."""
    return sample_ohlcv_uptrend["close"]


@pytest.fixture
def mock_binance_response():
    """Mock Binance klines API response (10 candles)."""
    base_time = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    candles = []
    price = 40000.0
    
    for i in range(10):
        open_price = price + np.random.uniform(-50, 50)
        close_price = price + np.random.uniform(-50, 50)
        high_price = max(open_price, close_price) + np.random.uniform(0, 30)
        low_price = min(open_price, close_price) - np.random.uniform(0, 30)
        volume = np.random.uniform(100, 500)
        
        candles.append([
            base_time + i * 60000,           # open time
            str(open_price),                  # open
            str(high_price),                  # high
            str(low_price),                   # low
            str(close_price),                 # close
            str(volume),                      # volume
            base_time + (i + 1) * 60000 - 1,  # close time
            str(volume * close_price),        # quote volume
            100,                              # trades
            str(volume * 0.5),                # taker buy base
            str(volume * 0.5 * close_price),  # taker buy quote
            "0",                              # ignore
        ])
        price = close_price
    
    return candles


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before each test."""
    from utils.cache import cache
    cache.clear()
    yield
    cache.clear()
