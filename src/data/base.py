from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Candle


class CandleFeed(ABC):
    @abstractmethod
    def get_recent_candles(self, symbol: str, limit: int) -> list[Candle]:
        """Retorna os candles mais recentes de um ativo."""
