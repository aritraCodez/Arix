"""
Unit tests for technical indicator calculations.
Tests RSI, MACD, and EMA with known data patterns.
"""

import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_ema,
    calculate_ema_trend,
    compute_all_indicators,
    IndicatorSignal,
)


class TestRSI:
    """Tests for RSI calculation."""

    def test_rsi_uptrend_is_high(self, sample_ohlcv_uptrend):
        """RSI should be relatively high in an uptrend."""
        result = calculate_rsi(sample_ohlcv_uptrend["close"], period=14)
        # In a strong uptrend, RSI should be above 50
        assert result.value > 50
        assert 0 <= result.value <= 100

    def test_rsi_downtrend_is_low(self, sample_ohlcv_downtrend):
        """RSI should be relatively low in a downtrend."""
        result = calculate_rsi(sample_ohlcv_downtrend["close"], period=14)
        # In a strong downtrend, RSI should be below 50
        assert result.value < 50
        assert 0 <= result.value <= 100

    def test_rsi_value_range(self, sample_close_prices):
        """RSI should always be between 0 and 100."""
        result = calculate_rsi(sample_close_prices)
        assert 0 <= result.value <= 100

    def test_rsi_oversold_signal(self):
        """RSI below 30 should give BULLISH signal (oversold → expect reversal)."""
        # Create a series that drops sharply
        prices = pd.Series([100] * 5 + [100 - i * 3 for i in range(20)])
        result = calculate_rsi(prices, period=14)
        if result.value < 30:
            assert result.signal == IndicatorSignal.BULLISH

    def test_rsi_overbought_signal(self):
        """RSI above 70 should give BEARISH signal (overbought → expect reversal)."""
        prices = pd.Series([100] * 5 + [100 + i * 3 for i in range(20)])
        result = calculate_rsi(prices, period=14)
        if result.value > 70:
            assert result.signal == IndicatorSignal.BEARISH

    def test_rsi_insufficient_data(self):
        """RSI should raise ValueError with too few data points."""
        prices = pd.Series([100, 101, 102])
        with pytest.raises(ValueError, match="Need at least"):
            calculate_rsi(prices, period=14)

    def test_rsi_flat_prices(self):
        """RSI with completely flat prices should handle gracefully."""
        prices = pd.Series([100.0] * 50)
        result = calculate_rsi(prices, period=14)
        # With no change, RSI should be neutral-ish
        assert 0 <= result.value <= 100


class TestMACD:
    """Tests for MACD calculation."""

    def test_macd_uptrend_bullish(self):
        """MACD should be bullish in a clean uptrend."""
        # Use a deterministic monotonic uptrend (no noise)
        prices = pd.Series([100 + i * 0.5 for i in range(100)])
        result = calculate_macd(prices)
        assert result.signal == IndicatorSignal.BULLISH
        assert result.histogram > 0

    def test_macd_downtrend_bearish(self, sample_ohlcv_downtrend):
        """MACD should be bearish in downtrend."""
        result = calculate_macd(sample_ohlcv_downtrend["close"])
        assert result.signal == IndicatorSignal.BEARISH
        assert result.histogram < 0

    def test_macd_returns_all_components(self, sample_close_prices):
        """MACD should return value, signal line, and histogram."""
        result = calculate_macd(sample_close_prices)
        assert hasattr(result, "value")
        assert hasattr(result, "signal_line")
        assert hasattr(result, "histogram")
        # Histogram should equal MACD - signal line
        assert abs(result.histogram - (result.value - result.signal_line)) < 1e-10

    def test_macd_insufficient_data(self):
        """MACD should raise ValueError with too few data points."""
        prices = pd.Series([100, 101, 102, 103, 104])
        with pytest.raises(ValueError, match="Need at least"):
            calculate_macd(prices)

    def test_macd_to_dict(self, sample_close_prices):
        """MACD to_dict should return correct keys."""
        result = calculate_macd(sample_close_prices)
        d = result.to_dict()
        assert "value" in d
        assert "signal_line" in d
        assert "histogram" in d
        assert "signal" in d


class TestEMA:
    """Tests for EMA and EMA trend calculations."""

    def test_ema_basic(self):
        """EMA should smooth the price series."""
        prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ema = calculate_ema(prices, period=3)
        # EMA should be between min and max
        assert ema.iloc[-1] >= prices.min()
        assert ema.iloc[-1] <= prices.max()

    def test_ema_trend_uptrend(self, sample_ohlcv_uptrend):
        """EMA trend should be bullish in uptrend."""
        result = calculate_ema_trend(sample_ohlcv_uptrend["close"])
        assert result.signal == IndicatorSignal.BULLISH
        assert result.short_ema > result.long_ema

    def test_ema_trend_downtrend(self, sample_ohlcv_downtrend):
        """EMA trend should be bearish in downtrend."""
        result = calculate_ema_trend(sample_ohlcv_downtrend["close"])
        assert result.signal == IndicatorSignal.BEARISH
        assert result.short_ema < result.long_ema

    def test_ema_trend_insufficient_data(self):
        """EMA trend should raise ValueError with too few data points."""
        prices = pd.Series([100, 101, 102])
        with pytest.raises(ValueError, match="Need at least"):
            calculate_ema_trend(prices)

    def test_ema_trend_to_dict(self, sample_close_prices):
        """EMA trend to_dict should return correct keys."""
        result = calculate_ema_trend(sample_close_prices)
        d = result.to_dict()
        assert "short" in d
        assert "long" in d
        assert "signal" in d


class TestComputeAll:
    """Tests for compute_all_indicators."""

    def test_compute_all_returns_all_indicators(self, sample_close_prices):
        """Should return results for all three indicators."""
        result = compute_all_indicators(sample_close_prices)
        assert result.rsi is not None
        assert result.macd is not None
        assert result.ema_trend is not None

    def test_compute_all_to_dict(self, sample_close_prices):
        """to_dict should return complete nested structure."""
        result = compute_all_indicators(sample_close_prices)
        d = result.to_dict()
        assert "rsi" in d
        assert "macd" in d
        assert "ema_trend" in d
        # Check nested keys
        assert "value" in d["rsi"]
        assert "signal" in d["rsi"]
        assert "value" in d["macd"]
        assert "histogram" in d["macd"]
        assert "short" in d["ema_trend"]
        assert "long" in d["ema_trend"]
