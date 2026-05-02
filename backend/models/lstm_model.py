"""
LSTM model architecture for price prediction.
Predicts the probability of upward price movement using the last N candles.
"""

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:
    class PriceLSTM(nn.Module):
        """
        LSTM-based model for binary price direction prediction.
        
        Input: Sequence of OHLCV features (normalized)
        Output: Probability of upward price movement [0, 1]
        """

        def __init__(
            self,
            input_size: int = 5,     # OHLCV features
            hidden_size: int = 64,
            num_layers: int = 2,
            dropout: float = 0.2,
        ):
            super().__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )

            self.classifier = nn.Sequential(
                nn.Linear(hidden_size, 32),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(32, 1),
                nn.Sigmoid(),  # Output probability [0, 1]
            )

        def forward(self, x):
            """
            Forward pass.
            
            Args:
                x: Tensor of shape (batch_size, sequence_length, input_size)
            
            Returns:
                Tensor of shape (batch_size, 1) — probability of upward movement
            """
            # LSTM forward
            lstm_out, (h_n, c_n) = self.lstm(x)

            # Use last hidden state
            last_hidden = lstm_out[:, -1, :]

            # Classify
            output = self.classifier(last_hidden)
            return output
else:
    PriceLSTM = None
