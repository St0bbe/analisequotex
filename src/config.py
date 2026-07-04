from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    timeframe: str = "M1"
    timeframe_seconds: int = 60
    candle_limit: int = 240
    symbols: tuple[str, ...] = field(
        default_factory=lambda: (
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "EURUSD-OTC",
            "GBPUSD-OTC",
            "USDJPY-OTC",
        )
    )

    rsi_period: int = 14
    fast_ma_period: int = 9
    slow_ma_period: int = 21
    ema_trend_period: int = 50
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    min_confidence: float = 0.72


def get_settings() -> Settings:
    return Settings()
