"""
Integration tests for the FastAPI /signal endpoint.
"""

import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def _mock_ohlcv_df(n=100):
    """Create a mock OHLCV DataFrame."""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.normal(0.05, 0.5, n))
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC"),
        "open": close - 0.1, "high": close + 0.3,
        "low": close - 0.3, "close": close,
        "volume": np.random.uniform(1000, 5000, n),
    })


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestSignalEndpoint:
    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_valid_crypto_signal(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df()
        resp = client.get("/signal?symbol=BTCUSDT&type=crypto&risk=medium")
        assert resp.status_code == 200
        data = resp.json()
        assert data["signal"] in ["UP", "DOWN", "NO_TRADE"]
        assert 0 <= data["confidence"] <= 100
        assert "rsi" in data["indicators"]
        assert "macd" in data["indicators"]
        assert "ema_trend" in data["indicators"]

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_valid_forex_signal(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df()
        resp = client.get("/signal?symbol=EURUSD&type=forex&risk=low")
        assert resp.status_code == 200

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_valid_stock_signal(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df()
        resp = client.get("/signal?symbol=AAPL&type=stock&risk=high")
        assert resp.status_code == 200

    def test_missing_symbol(self):
        resp = client.get("/signal?type=crypto")
        assert resp.status_code == 422

    def test_missing_type(self):
        resp = client.get("/signal?symbol=BTCUSDT")
        assert resp.status_code == 422

    def test_invalid_type(self):
        resp = client.get("/signal?symbol=BTCUSDT&type=invalid")
        assert resp.status_code == 422

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_insufficient_data(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df(n=10)
        resp = client.get("/signal?symbol=BTCUSDT&type=crypto")
        assert resp.status_code == 422

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_caching(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df()
        r1 = client.get("/signal?symbol=BTCUSDT&type=crypto")
        r2 = client.get("/signal?symbol=BTCUSDT&type=crypto")
        assert r1.json() == r2.json()
        assert mock_fetch.call_count == 1  # Second request served from cache

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_data_source_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("API down")
        resp = client.get("/signal?symbol=BTCUSDT&type=crypto")
        assert resp.status_code == 500

    @patch("routers.signals.fetch_ohlcv", new_callable=AsyncMock)
    def test_response_schema(self, mock_fetch):
        mock_fetch.return_value = _mock_ohlcv_df()
        resp = client.get("/signal?symbol=BTCUSDT&type=crypto")
        data = resp.json()
        assert data["asset"]["symbol"] == "BTCUSDT"
        assert data["asset"]["type"] == "crypto"
        assert data["risk_level"] == "medium"
        assert "ml_prediction" in data
        assert "timestamp" in data
