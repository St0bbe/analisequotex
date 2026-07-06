from __future__ import annotations

import csv
from pathlib import Path


class ResultLogger:
    def __init__(self, output_path: str = "signal_results.csv") -> None:
        self.output_path = Path(output_path)

    def append_many(self, rows: list[dict]) -> None:
        if not rows:
            return

        file_exists = self.output_path.exists()
        fieldnames = [
            "created_at",
            "evaluated_at",
            "feed",
            "symbol",
            "side",
            "confidence",
            "entry_price",
            "exit_close",
            "result",
            "reason",
        ]

        with self.output_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerows(rows)
