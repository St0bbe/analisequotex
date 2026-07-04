from __future__ import annotations

import pandas as pd

from src.models import Candle


def candles_to_dataframe(candles: list[Candle]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": candle.timestamp,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
            }
            for candle in candles
        ]
    )


def add_moving_average(df: pd.DataFrame, period: int, column_name: str) -> pd.DataFrame:
    df[column_name] = df["close"].rolling(window=period).mean()
    return df


def add_ema(df: pd.DataFrame, period: int, column_name: str) -> pd.DataFrame:
    df[column_name] = df["close"].ewm(span=period, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
    middle = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["bb_middle"] = middle
    df["bb_upper"] = middle + (std * std_multiplier)
    df["bb_lower"] = middle - (std * std_multiplier)
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    return df


def add_volatility(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    candle_range = df["high"] - df["low"]
    df["volatility"] = candle_range.rolling(window=period).mean()
    return df
