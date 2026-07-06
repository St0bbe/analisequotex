from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.data.base import CandleFeed
from src.models import Candle


class CsvCandleFeed(CandleFeed):
    def __init__(self, data_dir: Path | str = "data") -> None:
        self.data_dir = Path(data_dir)

    def get_recent_candles(self, symbol: str, limit: int) -> list[Candle]:
        path = self._path_for_symbol(symbol)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo de candles nao encontrado: {path}")

        candles: list[Candle] = []

        with path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                candles.append(
                    Candle(
                        timestamp=self._parse_timestamp(row["timestamp"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                    )
                )

        return candles[-limit:]

    def _path_for_symbol(self, symbol: str) -> Path:
        filename = symbol.lower().replace("-", "_") + "_m1.csv"
        return self.data_dir / filename

    def _parse_timestamp(self, value: str) -> datetime:
        return datetime.fromisoformat(value)
