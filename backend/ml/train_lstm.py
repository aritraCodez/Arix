"""
LSTM model training script.
Downloads historical data from Binance, prepares sequences,
and trains a binary price direction classifier.

Usage:
    python train_lstm.py --symbol BTCUSDT --epochs 50
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import httpx

# Add backend root to path for model import (train_lstm.py lives in backend/ml/)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def fetch_training_data(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 1000) -> pd.DataFrame:
    """Fetch historical OHLCV data from Binance."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    print(f"Fetching {limit} candles for {symbol} ({interval})...")
    response = httpx.get(url, params=params, timeout=30)
    response.raise_for_status()

    df = pd.DataFrame(response.json(), columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore",
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    print(f"Fetched {len(df)} candles")
    return df[["open", "high", "low", "close", "volume"]]


def prepare_sequences(df: pd.DataFrame, seq_length: int = 50):
    """Create input sequences and binary labels."""
    data = df[["open", "high", "low", "close", "volume"]].values.astype(np.float64)

    sequences = []
    labels = []

    for i in range(len(data) - seq_length - 1):
        seq = data[i:i + seq_length].copy()

        # Normalize by first close in sequence
        first_close = seq[0, 3]
        if first_close != 0:
            seq[:, :4] = (seq[:, :4] / first_close) - 1.0

        # Normalize volume
        mean_vol = seq[:, 4].mean()
        if mean_vol != 0:
            seq[:, 4] = seq[:, 4] / mean_vol

        # Label: 1 if next candle closes higher, 0 otherwise
        next_close = data[i + seq_length, 3]
        current_close = data[i + seq_length - 1, 3]
        label = 1.0 if next_close > current_close else 0.0

        sequences.append(seq)
        labels.append(label)

    X = np.array(sequences, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)

    print(f"Created {len(X)} sequences (seq_length={seq_length})")
    print(f"Label distribution: UP={y.sum():.0f} ({y.mean()*100:.1f}%), DOWN={len(y)-y.sum():.0f}")
    return X, y


def train_model(X, y, epochs=50, lr=0.001, batch_size=32, save_path="saved_models/lstm_model.pt"):
    """Train the LSTM model."""
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import TensorDataset, DataLoader
    except ImportError:
        print("ERROR: PyTorch is required. Install with: pip install torch")
        sys.exit(1)

    from models.lstm_model import PriceLSTM

    # Train/val split (80/20)
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    val_ds = TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    # Model
    model = PriceLSTM(input_size=5, hidden_size=64, num_layers=2)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print(f"\nTraining LSTM model ({sum(p.numel() for p in model.parameters())} params)")
    print(f"Train: {len(X_train)} samples, Val: {len(X_val)} samples\n")

    best_val_loss = float("inf")

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            pred = model(batch_X).squeeze()
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                pred = model(batch_X).squeeze()
                val_loss += criterion(pred, batch_y).item()
                predicted = (pred > 0.5).float()
                correct += (predicted == batch_y).sum().item()
                total += batch_y.size(0)

        avg_train = train_loss / len(train_loader)
        avg_val = val_loss / len(val_loader)
        accuracy = correct / total * 100

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | "
                  f"Train Loss: {avg_train:.4f} | "
                  f"Val Loss: {avg_val:.4f} | "
                  f"Val Acc: {accuracy:.1f}%")

        # Save best model
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), save_path)

    print(f"\nBest validation loss: {best_val_loss:.4f}")
    print(f"Model saved to: {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Train LSTM price prediction model")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair")
    parser.add_argument("--interval", default="1h", help="Candle interval")
    parser.add_argument("--limit", type=int, default=1000, help="Number of candles")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--seq-length", type=int, default=50, help="Sequence length")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_output = os.path.join(script_dir, "saved_models", "lstm_model.pt")

    parser.add_argument("--output", default=default_output, help="Model save path")
    args = parser.parse_args()

    # Fetch data
    df = fetch_training_data(args.symbol, args.interval, args.limit)

    # Prepare sequences
    X, y = prepare_sequences(df, args.seq_length)

    # Train
    train_model(X, y, epochs=args.epochs, save_path=args.output)


if __name__ == "__main__":
    main()
