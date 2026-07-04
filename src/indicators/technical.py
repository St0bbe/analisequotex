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


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = true_range.rolling(window=period).mean()
    df["atr_ratio"] = df["atr"] / df["close"]
    return df


def add_stochastic(df: pd.DataFrame, period: int = 14, signal_period: int = 3) -> pd.DataFrame:
    lowest_low = df["low"].rolling(window=period).min()
    highest_high = df["high"].rolling(window=period).max()
    denominator = (highest_high - lowest_low).replace(0, pd.NA)
    df["stoch_k"] = 100 * ((df["close"] - lowest_low) / denominator)
    df["stoch_d"] = df["stoch_k"].rolling(window=signal_period).mean()
    df["stoch_k"] = df["stoch_k"].fillna(50)
    df["stoch_d"] = df["stoch_d"].fillna(50)
    return df


def add_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    body = (df["close"] - df["open"]).abs()
    full_range = (df["high"] - df["low"]).replace(0, pd.NA)
    df["body_ratio"] = (body / full_range).fillna(0)
    df["is_bullish_candle"] = df["close"] > df["open"]
    df["is_bearish_candle"] = df["close"] < df["open"]
    return df


def add_all_indicators(df: pd.DataFrame, settings) -> pd.DataFrame:
    df = add_moving_average(df, settings.fast_ma_period, "fast_ma")
    df = add_moving_average(df, settings.slow_ma_period, "slow_ma")
    df = add_ema(df, settings.ema_trend_period, "ema_trend")
    df = add_rsi(df, settings.rsi_period)
    df = add_bollinger_bands(df, settings.bollinger_period, settings.bollinger_std)
    df = add_macd(df)
    df = add_volatility(df, settings.atr_period)
    df = add_atr(df, settings.atr_period)
    df = add_stochastic(df, settings.stochastic_period, settings.stochastic_signal_period)
    df = add_candle_features(df)
    return df
