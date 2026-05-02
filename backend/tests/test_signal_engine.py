"""
Unit tests for the signal engine.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.indicators import (
    RSIResult, MACDResult, EMATrendResult, IndicatorResults, IndicatorSignal,
)
from services.signal_engine import (
    Signal, RiskLevel, generate_signal, _indicator_to_score,
    _rsi_to_refined_score, RISK_THRESHOLDS,
)


def _make_indicators(
    rsi_value=50.0, rsi_signal=IndicatorSignal.NEUTRAL,
    macd_signal=IndicatorSignal.NEUTRAL, macd_hist=0.0,
    ema_signal=IndicatorSignal.NEUTRAL, ema_short=100.0, ema_long=100.0,
) -> IndicatorResults:
    return IndicatorResults(
        rsi=RSIResult(value=rsi_value, signal=rsi_signal),
        macd=MACDResult(value=0.0, signal_line=0.0, histogram=macd_hist, signal=macd_signal),
        ema_trend=EMATrendResult(short_ema=ema_short, long_ema=ema_long, signal=ema_signal),
    )


class TestScoring:
    def test_bullish_score(self):
        assert _indicator_to_score(IndicatorSignal.BULLISH) == 1.0

    def test_bearish_score(self):
        assert _indicator_to_score(IndicatorSignal.BEARISH) == -1.0

    def test_neutral_score(self):
        assert _indicator_to_score(IndicatorSignal.NEUTRAL) == 0.0

    def test_rsi_oversold(self):
        assert _rsi_to_refined_score(15, IndicatorSignal.BULLISH) == 1.0

    def test_rsi_overbought(self):
        assert _rsi_to_refined_score(85, IndicatorSignal.BEARISH) == -1.0


class TestSignalGeneration:
    def test_all_bullish_returns_up(self):
        indicators = _make_indicators(
            rsi_value=25, rsi_signal=IndicatorSignal.BULLISH,
            macd_signal=IndicatorSignal.BULLISH, macd_hist=0.1,
            ema_signal=IndicatorSignal.BULLISH, ema_short=101, ema_long=100,
        )
        result = generate_signal(indicators, RiskLevel.HIGH, symbol="TEST", asset_type="crypto", timestamp="T")
        assert result.signal == Signal.UP

    def test_all_bearish_returns_down(self):
        indicators = _make_indicators(
            rsi_value=75, rsi_signal=IndicatorSignal.BEARISH,
            macd_signal=IndicatorSignal.BEARISH, macd_hist=-0.1,
            ema_signal=IndicatorSignal.BEARISH, ema_short=99, ema_long=100,
        )
        result = generate_signal(indicators, RiskLevel.HIGH, symbol="TEST", asset_type="crypto", timestamp="T")
        assert result.signal == Signal.DOWN

    def test_all_neutral_returns_no_trade(self):
        indicators = _make_indicators()
        result = generate_signal(indicators, RiskLevel.MEDIUM, symbol="TEST", asset_type="crypto", timestamp="T")
        assert result.signal == Signal.NO_TRADE

    def test_low_risk_filters_weak(self):
        indicators = _make_indicators(macd_signal=IndicatorSignal.BULLISH, macd_hist=0.05)
        result = generate_signal(indicators, RiskLevel.LOW, symbol="TEST", asset_type="crypto", timestamp="T")
        assert result.signal == Signal.NO_TRADE

    def test_confidence_range(self):
        for sig in [IndicatorSignal.BULLISH, IndicatorSignal.BEARISH, IndicatorSignal.NEUTRAL]:
            indicators = _make_indicators(rsi_value=25, rsi_signal=sig, macd_signal=sig, ema_signal=sig)
            result = generate_signal(indicators, RiskLevel.MEDIUM, symbol="T", asset_type="crypto", timestamp="T")
            assert 0 <= result.confidence <= 100

    def test_ml_integration(self):
        indicators = _make_indicators()
        r1 = generate_signal(indicators, RiskLevel.HIGH, symbol="T", asset_type="crypto", timestamp="T")
        r2 = generate_signal(indicators, RiskLevel.HIGH, ml_probability=0.95, symbol="T", asset_type="crypto", timestamp="T")
        assert r2.confidence >= r1.confidence

    def test_result_schema(self):
        indicators = _make_indicators()
        d = generate_signal(indicators, RiskLevel.MEDIUM, symbol="BTC", asset_type="crypto", timestamp="T").to_dict()
        for key in ["signal", "confidence", "indicators", "ml_prediction", "risk_level", "asset", "timestamp"]:
            assert key in d


class TestRiskThresholds:
    def test_ordering(self):
        assert RISK_THRESHOLDS[RiskLevel.LOW] > RISK_THRESHOLDS[RiskLevel.MEDIUM] > RISK_THRESHOLDS[RiskLevel.HIGH]
