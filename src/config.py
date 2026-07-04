from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    symbol: str = "EURUSD"
    candle_limit: int = 120
    rsi_period: int = 14
    fast_ma_period: int = 9
    slow_ma_period: int = 21


def get_settings() -> Settings:
    return Settings()
