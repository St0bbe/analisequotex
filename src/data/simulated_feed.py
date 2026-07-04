from __future__ import annotations

from datetime import datetime, timedelta
import math
import random

from src.models import Candle


class SimulatedCandleFeed:
    def __init__(self, initial_price: float = 1.1000) -> None:
        self.initial_price = initial_price

    def get_recent_candles(self, limit: int) -> list[Candle]:
        now = datetime.utcnow().replace(second=0, microsecond=0)
        candles: list[Candle] = []
        price = self.initial_price

        for index in range(limit):
            wave = math.sin(index / 8) * 0.0015
            noise = random.uniform(-0.0006, 0.0006)
            candle_open = price
            candle_close = self.initial_price + wave + noise
            candle_high = max(candle_open, candle_close) + random.uniform(0.0001, 0.0005)
            candle_low = min(candle_open, candle_close) - random.uniform(0.0001, 0.0005)
            price = candle_close

            candles.append(
                Candle(
                    timestamp=now - timedelta(minutes=limit - index),
                    open=round(candle_open, 5),
                    high=round(candle_high, 5),
                    low=round(candle_low, 5),
                    close=round(candle_close, 5),
                )
            )

        return candles
