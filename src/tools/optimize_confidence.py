from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

from src.backtesting import CsvBacktester
from src.config import get_settings


DATA_DIR = Path("data")
REPORT_PATH = Path("confidence_optimization_report.csv")

SYMBOL_FILES = {
    "EURUSD": "eurusd_m1.csv",
    "GBPUSD": "gbpusd_m1.csv",
    "USDJPY": "usdjpy_m1.csv",
    "EURUSD-OTC": "eurusd_otc_m1.csv",
    "GBPUSD-OTC": "gbpusd_otc_m1.csv",
    "USDJPY-OTC": "usdjpy_otc_m1.csv",
}

CONFIDENCE_LEVELS = [0.58, 0.62, 0.66, 0.70, 0.74, 0.78, 0.82, 0.86]


def main() -> None:
    base_settings = get_settings()
    rows: list[dict] = []

    for confidence in CONFIDENCE_LEVELS:
        settings = replace(base_settings, min_confidence=confidence)

        for symbol, filename in SYMBOL_FILES.items():
            csv_path = DATA_DIR / filename

            if not csv_path.exists():
                print(f"Pulando {symbol}: arquivo nao encontrado em {csv_path}")
                continue

            summary = CsvBacktester(str(csv_path), symbol, settings=settings).run(lookahead_candles=1)
            row = summary.to_dict()
            row["min_confidence"] = confidence
            rows.append(row)

            print(
                f"{symbol} | confianca {confidence:.2f} | "
                f"acerto {summary.accuracy:.2%} | sinais {summary.total_signals}"
            )

    if not rows:
        print("Nenhum resultado gerado. Execute antes: python -m src.tools.generate_sample_data")
        return

    fieldnames = ["min_confidence"] + [key for key in rows[0].keys() if key != "min_confidence"]

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Relatorio de otimizacao salvo em {REPORT_PATH}")


if __name__ == "__main__":
    main()
