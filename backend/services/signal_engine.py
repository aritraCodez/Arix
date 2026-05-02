"""
Signal engine — combines technical indicators and optional ML predictions
into a weighted trading signal (UP / DOWN / NO_TRADE).
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from services.indicators import IndicatorResults, IndicatorSignal

logger = logging.getLogger(__name__)


class Signal(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NO_TRADE = "NO_TRADE"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Confidence thresholds per risk level
# LOW = only high-confidence signals, HIGH = more frequent signals
RISK_THRESHOLDS = {
    RiskLevel.LOW: 75,
    RiskLevel.MEDIUM: 55,
    RiskLevel.HIGH: 35,
}

# Indicator weights without ML
WEIGHTS_NO_ML = {
    "rsi": 0.30,
    "macd": 0.35,
    "ema_trend": 0.35,
}

# Indicator weights with ML
WEIGHTS_WITH_ML = {
    "rsi": 0.20,
    "macd": 0.25,
    "ema_trend": 0.20,
    "ml": 0.35,
}


@dataclass
class SignalResult:
    signal: Signal
    confidence: int
    leaning: str
    up_percent: int
    down_percent: int
    indicators: dict
    ml_prediction: Optional[dict]
    ai_analysis: Optional[dict]
    risk_level: str
    asset: dict
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "signal": self.signal.value,
            "confidence": self.confidence,
            "leaning": self.leaning,
            "up_percent": self.up_percent,
            "down_percent": self.down_percent,
            "indicators": self.indicators,
            "ml_prediction": self.ml_prediction,
            "ai_analysis": self.ai_analysis,
            "risk_level": self.risk_level,
            "asset": self.asset,
            "timestamp": self.timestamp,
        }


def _indicator_to_score(signal: IndicatorSignal) -> float:
    """
    Convert indicator signal to a numeric score.
    BULLISH = +1, BEARISH = -1, NEUTRAL = 0
    """
    mapping = {
        IndicatorSignal.BULLISH: 1.0,
        IndicatorSignal.BEARISH: -1.0,
        IndicatorSignal.NEUTRAL: 0.0,
    }
    return mapping.get(signal, 0.0)


def _rsi_to_refined_score(rsi_value: float, rsi_signal: IndicatorSignal) -> float:
    """
    Produce a more granular RSI score based on the actual RSI value.
    
    - RSI < 20:  strong bullish (+1.0)
    - RSI 20-30: bullish (+0.7)
    - RSI 30-40: slightly bullish (+0.3)
    - RSI 40-60: neutral (0.0)
    - RSI 60-70: slightly bearish (-0.3)
    - RSI 70-80: bearish (-0.7)
    - RSI > 80:  strong bearish (-1.0)
    """
    if rsi_value < 20:
        return 1.0
    elif rsi_value < 30:
        return 0.7
    elif rsi_value < 40:
        return 0.3
    elif rsi_value <= 60:
        return 0.0
    elif rsi_value <= 70:
        return -0.3
    elif rsi_value <= 80:
        return -0.7
    else:
        return -1.0


def generate_signal(
    indicators: IndicatorResults,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    ml_probability: Optional[float] = None,
    ai_result: Optional[dict] = None,
    symbol: str = "",
    asset_type: str = "",
    timestamp: str = "",
) -> SignalResult:
    """
    Combine technical indicators, optional ML prediction, and optional AI analysis
    into a weighted trading signal.
    
    Args:
        indicators: Computed indicator results
        risk_level: Risk tolerance level
        ml_probability: Optional ML predicted probability of upward movement [0, 1]
        ai_result: Optional AI analysis dict with 'score' key [-1.0, 1.0]
        symbol: Asset symbol
        asset_type: Asset type string
        timestamp: ISO format timestamp
    
    Returns:
        SignalResult with signal direction, confidence, and metadata
    """
    use_ml = ml_probability is not None
    use_ai = ai_result is not None and "score" in (ai_result or {})
    
    # Calculate individual scores
    rsi_score = _rsi_to_refined_score(indicators.rsi.value, indicators.rsi.signal)
    macd_score = _indicator_to_score(indicators.macd.signal)
    ema_score = _indicator_to_score(indicators.ema_trend.signal)
    # 3. Calculate Confidence (Weighted Average)
    # Weights optimized for 1m scalping — redistributed based on available sources
    if use_ml and use_ai:
        weights = {
            "rsi": 0.15, "macd": 0.15, "ema": 0.20,
            "bollinger": 0.10, "ml": 0.15, "ai": 0.25
        }
    elif use_ai:
        weights = {
            "rsi": 0.25, "macd": 0.25, "ema": 0.25,
            "bollinger": 0.10, "ai": 0.15
        }
    elif use_ml:
        weights = {
            "rsi": 0.20, "macd": 0.20, "ema": 0.30,
            "bollinger": 0.10, "ml": 0.20
        }
    else:
        weights = {
            "rsi": 0.25, "macd": 0.25, "ema": 0.40,
            "bollinger": 0.10
        }
    
    # Bollinger Logic
    last_price = indicators.raw_prices[-1]
    b = indicators.bollinger
    bb_score = 0.0
    if last_price > b["upper"]: bb_score = 1.0 
    elif last_price < b["lower"]: bb_score = -1.0 

    weighted_score = (
        (rsi_score * weights["rsi"]) +
        (macd_score * weights["macd"]) +
        (ema_score * weights["ema"]) +
        (bb_score * weights["bollinger"])
    )

    if use_ml:
        ml_score = (ml_probability - 0.5) * 2.0
        weighted_score += weights["ml"] * ml_score

    if use_ai:
        ai_score_val = float(ai_result["score"])
        weighted_score += weights["ai"] * ai_score_val

    # Add Micro-Momentum (Real-time flicker)
    # Compare current close to previous close for immediate sentiment
    if len(indicators.raw_prices) >= 2:
        last_price = indicators.raw_prices[-1]
        prev_price = indicators.raw_prices[-2]
        momentum = (last_price - prev_price) / prev_price if prev_price != 0 else 0
        # Map momentum to a small flicker score [-0.1, +0.1]
        flicker = max(-0.1, min(0.1, momentum * 1000)) 
        weighted_score += flicker

    # Calculate separate predictions
    up_percent = int(((weighted_score + 1) / 2) * 100)
    down_percent = 100 - up_percent
    
    # Confidence is the strength of the winner
    confidence = int(abs(weighted_score) * 100)

    # Determine signal direction
    threshold = RISK_THRESHOLDS[risk_level]
    leaning = "UP" if weighted_score > 0 else "DOWN"

    if confidence < threshold:
        signal = Signal.NO_TRADE
    elif weighted_score > 0:
        signal = Signal.UP
    else:
        signal = Signal.DOWN

    # Build ML prediction dict
    ml_prediction = None
    if use_ml:
        ml_prediction = {
            "probability": round(ml_probability, 4),
            "enabled": True,
        }
    else:
        ml_prediction = {
            "probability": None,
            "enabled": False,
        }

    # Build AI analysis dict
    ai_analysis = None
    if use_ai:
        ai_analysis = ai_result  # already has score, reasoning, confidence, model, etc.
    else:
        ai_analysis = {
            "enabled": False,
            "score": None,
            "reasoning": None,
        }

    logger.info(
        f"Signal for {symbol}: {signal.value} (confidence={confidence}%, "
        f"risk={risk_level.value}, rsi={rsi_score:.2f}, macd={macd_score:.2f}, "
        f"ema={ema_score:.2f}, ml={'enabled' if use_ml else 'disabled'}, "
        f"ai={'enabled' if use_ai else 'disabled'})"
    )

    return SignalResult(
        signal=signal,
        confidence=confidence,
        leaning=leaning,
        up_percent=up_percent,
        down_percent=down_percent,
        indicators=indicators.to_dict(),
        ml_prediction=ml_prediction,
        ai_analysis=ai_analysis,
        risk_level=risk_level.value,
        asset={"symbol": symbol, "type": asset_type},
        timestamp=timestamp,
    )
