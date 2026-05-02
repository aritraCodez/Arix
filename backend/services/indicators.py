"""
Technical indicator calculations.
Pure Python + Pandas implementations — no external indicator library dependency.
Implements RSI, MACD, and EMA with standard financial formulas.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class IndicatorSignal(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class RSIResult:
    value: float
    signal: IndicatorSignal

    def to_dict(self) -> dict:
        return {"value": round(self.value, 2), "signal": self.signal.value}


@dataclass
class MACDResult:
    value: float
    signal_line: float
    histogram: float
    signal: IndicatorSignal

    def to_dict(self) -> dict:
        return {
            "value": round(self.value, 6),
            "signal_line": round(self.signal_line, 6),
            "histogram": round(self.histogram, 6),
            "signal": self.signal.value,
        }


@dataclass
class EMATrendResult:
    short_ema: float
    long_ema: float
    value: float  # -1.0 to 1.0
    signal: IndicatorSignal

    def to_dict(self) -> dict:
        return {
            "short": round(self.short_ema, 6),
            "long": round(self.long_ema, 6),
            "value": self.value,
            "signal": self.signal.value,
        }


@dataclass
class IndicatorResults:
    """Container for all calculated indicators."""
    rsi: RSIResult
    macd: MACDResult
    ema_trend: EMATrendResult
    bollinger: Dict[str, float]  # New: upper, middle, lower
    raw_prices: List[float] = None

    def to_dict(self) -> dict:
        return {
            "rsi": self.rsi.to_dict(),
            "macd": self.macd.to_dict(),
            "ema_trend": self.ema_trend.to_dict(),
            "bollinger": self.bollinger,
        }


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Uses the standard EMA formula:
    EMA = price * multiplier + EMA_prev * (1 - multiplier)
    where multiplier = 2 / (period + 1)
    
    Args:
        series: Price series (typically close prices)
        period: EMA period
    
    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(close_prices: pd.Series, period: int = 14) -> RSIResult:
    """
    Calculate Relative Strength Index using Wilder's smoothing method.
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        close_prices: Series of closing prices
        period: RSI period (default 14)
    
    Returns:
        RSIResult with value and signal classification
    
    Raises:
        ValueError: If insufficient data
    """
    if len(close_prices) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} data points for RSI({period}), "
            f"got {len(close_prices)}"
        )

    # Calculate price changes
    delta = close_prices.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Wilder's smoothing (equivalent to EMA with alpha = 1/period)
    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Get latest RSI value
    current_rsi = float(rsi.iloc[-1])

    # Handle NaN
    if np.isnan(current_rsi):
        return RSIResult(value=50.0, signal=IndicatorSignal.NEUTRAL)

    # Classify signal
    if current_rsi < 30:
        signal = IndicatorSignal.BULLISH  # Oversold → expect reversal up
    elif current_rsi > 70:
        signal = IndicatorSignal.BEARISH  # Overbought → expect reversal down
    else:
        signal = IndicatorSignal.NEUTRAL

    return RSIResult(value=current_rsi, signal=signal)


def calculate_macd(
    close_prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """
    Calculate Moving Average Convergence Divergence.
    
    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line
    
    Args:
        close_prices: Series of closing prices
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)
    
    Returns:
        MACDResult with MACD value, signal line, histogram, and signal
    
    Raises:
        ValueError: If insufficient data
    """
    min_required = slow_period + signal_period
    if len(close_prices) < min_required:
        raise ValueError(
            f"Need at least {min_required} data points for MACD({fast_period},{slow_period},{signal_period}), "
            f"got {len(close_prices)}"
        )

    # Calculate MACD line
    ema_fast = calculate_ema(close_prices, fast_period)
    ema_slow = calculate_ema(close_prices, slow_period)
    macd_line = ema_fast - ema_slow

    # Signal line
    signal_line = calculate_ema(macd_line, signal_period)

    # Histogram
    histogram = macd_line - signal_line

    # Get latest values
    current_macd = float(macd_line.iloc[-1])
    current_signal = float(signal_line.iloc[-1])
    current_hist = float(histogram.iloc[-1])

    # Handle NaN
    if any(np.isnan(v) for v in [current_macd, current_signal, current_hist]):
        return MACDResult(
            value=0.0, signal_line=0.0, histogram=0.0,
            signal=IndicatorSignal.NEUTRAL,
        )

    # Classify signal
    # Bullish: MACD above signal line and histogram positive/increasing
    # Bearish: MACD below signal line and histogram negative/decreasing
    if current_hist > 0 and current_macd > current_signal:
        signal = IndicatorSignal.BULLISH
    elif current_hist < 0 and current_macd < current_signal:
        signal = IndicatorSignal.BEARISH
    else:
        signal = IndicatorSignal.NEUTRAL

    return MACDResult(
        value=current_macd,
        signal_line=current_signal,
        histogram=current_hist,
        signal=signal,
    )


def calculate_ema_trend(
    close_prices: pd.Series,
    short_period: int = 9,
    long_period: int = 21,
) -> EMATrendResult:
    """
    Calculate EMA trend using short and long EMAs.
    
    Bullish when short EMA > long EMA (uptrend).
    Bearish when short EMA < long EMA (downtrend).
    
    Args:
        close_prices: Series of closing prices
        short_period: Short EMA period (default 9)
        long_period: Long EMA period (default 21)
    
    Returns:
        EMATrendResult with short/long EMA values and signal
    
    Raises:
        ValueError: If insufficient data
    """
    if len(close_prices) < long_period:
        # Graceful fallback: return a neutral result instead of crashing
        return EMATrendResult(
            short_ema=0.0,
            long_ema=0.0,
            value=0.0,
            signal=IndicatorSignal.NEUTRAL
        )

    ema_short = close_prices.ewm(span=short_period, adjust=False).mean()
    ema_long = close_prices.ewm(span=long_period, adjust=False).mean()

    current_short = float(ema_short.iloc[-1])
    current_long = float(ema_long.iloc[-1])

    # Score from -1.0 to 1.0
    if current_short > current_long:
        value = 1.0
        signal = IndicatorSignal.BULLISH
    elif current_short < current_long:
        value = -1.0
        signal = IndicatorSignal.BEARISH
    else:
        value = 0.0
        signal = IndicatorSignal.NEUTRAL

    return EMATrendResult(
        short_ema=current_short,
        long_ema=current_long,
        value=value,
        signal=signal
    )


def calculate_bollinger_bands(close_prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """Calculate Bollinger Bands."""
    if len(close_prices) < period:
        last = float(close_prices.iloc[-1]) if not close_prices.empty else 0.0
        return {"upper": last, "middle": last, "lower": last}
    
    sma = close_prices.rolling(window=period).mean()
    std = close_prices.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        "upper": float(upper.iloc[-1]),
        "middle": float(sma.iloc[-1]),
        "lower": float(lower.iloc[-1])
    }


def compute_all_indicators(data) -> IndicatorResults:
    """Run all technical indicator calculations."""
    # Ensure we have a Series of close prices
    if isinstance(data, pd.DataFrame):
        close = data["close"]
    else:
        close = pd.Series(data)

    rsi = calculate_rsi(close)
    macd = calculate_macd(close)
    ema = calculate_ema_trend(close)
    bollinger = calculate_bollinger_bands(close)

    return IndicatorResults(
        rsi=rsi,
        macd=macd,
        ema_trend=ema,
        bollinger=bollinger,
        raw_prices=close.tail(10).tolist()
    )
