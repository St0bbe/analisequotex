from __future__ import annotations

import os
from datetime import datetime

import requests

from src.data.base import CandleFeed
from src.models import Candle


class OandaCandleFeed(CandleFeed):
    """Fonte de candles reais via OANDA REST v20.

    Requer variaveis de ambiente:
    - OANDA_API_TOKEN
    - OANDA_API_URL opcional. Padrao: https://api-fxpractice.oanda.com

    Observacao: OANDA cobre pares forex reais, como EUR_USD, GBP_USD e USD_JPY.
    Nao cobre ativos OTC especificos de plataformas como Quotex/Pocket Option.
    """

    SYMBOL_MAP = {
        "EURUSD": "EUR_USD",
        "GBPUSD": "GBP_USD",
        "USDJPY": "USD_JPY",
    }

    def __init__(self, granularity: str = "M1") -> None:
        self.api_token = os.getenv("OANDA_API_TOKEN")
        self.api_url = os.getenv("OANDA_API_URL", "https://api-fxpractice.oanda.com")
        self.granularity = granularity

        if not self.api_token:
            raise ValueError("OANDA_API_TOKEN nao configurado no ambiente.")

    def get_recent_candles(self, symbol: str, limit: int) -> list[Candle]:
        instrument = self._instrument_for(symbol)
        url = f"{self.api_url}/v3/instruments/{instrument}/candles"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {
            "count": min(limit, 5000),
            "price": "M",
            "granularity": self.granularity,
        }

        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()

        candles: list[Candle] = []
        for item in payload.get("candles", []):
            mid = item.get("mid")
            if not mid:
                continue

            candles.append(
                Candle(
                    timestamp=self._parse_time(item["time"]),
                    open=float(mid["o"]),
                    high=float(mid["h"]),
                    low=float(mid["l"]),
                    close=float(mid["c"]),
                )
            )

        return candles[-limit:]

    def _instrument_for(self, symbol: str) -> str:
        normalized = symbol.replace("-OTC", "")
        instrument = self.SYMBOL_MAP.get(normalized)

        if not instrument:
            raise ValueError(f"Ativo nao suportado pela OANDA: {symbol}")

        return instrument

    def _parse_time(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        if "." in normalized:
            head, tail = normalized.split(".", 1)
            timezone = "+00:00" if "+" in tail else ""
            fraction = tail.split("+")[0][:6]
            normalized = f"{head}.{fraction}{timezone}"
        return datetime.fromisoformat(normalized)
