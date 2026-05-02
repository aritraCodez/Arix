"""
ML predictor service.
Loads a trained LSTM model and produces price direction predictions.
Falls back gracefully if model is not available or torch is not installed.
"""

import logging
from typing import Optional
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Try importing torch
try:
    import torch
    from models.lstm_model import PriceLSTM
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed — ML predictions disabled")


class MLPredictor:
    """
    Manages LSTM model loading and inference.
    Returns None for predictions when model is unavailable.
    """

    def __init__(self, model_path: str = "", enabled: bool = False):
        self.enabled = enabled and TORCH_AVAILABLE
        self.model = None
        self.model_path = model_path
        self.sequence_length = 50
        self.device = "cpu"

        if self.enabled:
            self._load_model()

    def _load_model(self) -> None:
        """Attempt to load saved model weights."""
        path = Path(self.model_path)
        if not path.exists():
            logger.warning(f"ML model not found at {self.model_path} — predictions disabled")
            self.enabled = False
            return

        try:
            self.model = PriceLSTM(input_size=5, hidden_size=64, num_layers=2)
            self.model.load_state_dict(
                torch.load(self.model_path, map_location=self.device, weights_only=True)
            )
            self.model.eval()
            logger.info(f"ML model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model = None
            self.enabled = False

    def _normalize_data(self, df: pd.DataFrame) -> np.ndarray:
        """
        Normalize OHLCV data for model input.
        Uses percentage returns relative to the first candle.
        """
        features = df[["open", "high", "low", "close", "volume"]].values.astype(np.float64)

        # Normalize price columns by first close (percentage change)
        first_close = features[0, 3]  # close of first candle
        if first_close != 0:
            features[:, :4] = (features[:, :4] / first_close) - 1.0

        # Normalize volume by mean volume
        mean_vol = features[:, 4].mean()
        if mean_vol != 0:
            features[:, 4] = features[:, 4] / mean_vol

        return features

    def predict(self, df: pd.DataFrame) -> Optional[float]:
        """
        Predict probability of upward price movement.
        
        Args:
            df: OHLCV DataFrame with at least `sequence_length` rows
        
        Returns:
            Probability [0, 1] of upward movement, or None if unavailable
        """
        if not self.enabled or self.model is None:
            return None

        if len(df) < self.sequence_length:
            logger.warning(
                f"Insufficient data for ML prediction: {len(df)} < {self.sequence_length}"
            )
            return None

        try:
            # Use last N candles
            recent = df.tail(self.sequence_length).copy()
            features = self._normalize_data(recent)

            # Convert to tensor: (1, seq_len, features)
            x = torch.FloatTensor(features).unsqueeze(0).to(self.device)

            # Inference
            with torch.no_grad():
                probability = self.model(x).item()

            logger.info(f"ML prediction: {probability:.4f}")
            return float(probability)

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None


# Global predictor instance (initialized in main.py startup)
ml_predictor: Optional[MLPredictor] = None


def init_predictor(model_path: str, enabled: bool) -> MLPredictor:
    """Initialize the global ML predictor."""
    global ml_predictor
    ml_predictor = MLPredictor(model_path=model_path, enabled=enabled)
    return ml_predictor


def get_predictor() -> Optional[MLPredictor]:
    """Get the global ML predictor instance."""
    return ml_predictor
