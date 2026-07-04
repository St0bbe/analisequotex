from __future__ import annotations

import csv
from pathlib import Path

from src.models import MarketSignal


class SignalLogger:
    def __init__(self, output_path: str = "signals.csv") -> None:
        self.output_path = Path(output_path)

    def append_many(self, signals: list[MarketSignal]) -> None:
        file_exists = self.output_path.exists()

        with self.output_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["created_at", "symbol", "side", "confidence", "price", "reason"],
            )

            if not file_exists:
                writer.writeheader()

            for signal in signals:
                writer.writerow(
                    {
                        "created_at": signal.created_at.isoformat(),
                        "symbol": signal.symbol,
                        "side": signal.side.value,
                        "confidence": signal.confidence,
                        "price": signal.price,
                        "reason": signal.reason,
                    }
                )
