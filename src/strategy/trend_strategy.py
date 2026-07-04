from __future__ import annotations

from datetime import datetime

from src.config import Settings
from src.indicators.technical import add_moving_average, add_rsi, candles_to_dataframe
from src.models import Candle, MarketSignal, SignalSide


class TrendStrategy:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, candles: list[Candle]) -> MarketSignal:
        if len(candles) < self.settings.slow_ma_period + self.settings.rsi_period:
            last_price = candles[-1].close if candles else 0
            return MarketSignal(self.settings.symbol, SignalSide.WAIT, 0, "Dados insuficientes.", last_price, datetime.utcnow())

        df = candles_to_dataframe(candles)
        df = add_moving_average(df, self.settings.fast_ma_period, "fast_ma")
        df = add_moving_average(df, self.settings.slow_ma_period, "slow_ma")
        df = add_rsi(df, self.settings.rsi_period)

        last = df.iloc[-1]
        price = float(last["close"])
        fast_ma = float(last["fast_ma"])
        slow_ma = float(last["slow_ma"])
        rsi = float(last["rsi"])

        if fast_ma > slow_ma and 45 <= rsi <= 68:
            return MarketSignal(
                self.settings.symbol,
                SignalSide.BUY,
                0.70,
                f"Alerta educacional: tendencia de alta. RSI={rsi:.2f}.",
                price,
                datetime.utcnow(),
            )

        if fast_ma < slow_ma and 32 <= rsi <= 55:
            return MarketSignal(
                self.settings.symbol,
                SignalSide.SELL,
                0.70,
                f"Alerta educacional: tendencia de baixa. RSI={rsi:.2f}.",
                price,
                datetime.utcnow(),
            )

        return MarketSignal(
            self.settings.symbol,
            SignalSide.WAIT,
            0.40,
            f"Mercado sem confirmacao. RSI={rsi:.2f}.",
            price,
            datetime.utcnow(),
        )
