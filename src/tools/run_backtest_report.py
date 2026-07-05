from __future__ import annotations

import csv
from pathlib import Path

from src.backtesting import CsvBacktester


DATA_DIR = Path("data")
REPORT_PATH = Path("backtest_report.csv")


SYMBOL_FILES = {
    "EURUSD": "eurusd_m1.csv",
    "GBPUSD": "gbpusd_m1.csv",
    "USDJPY": "usdjpy_m1.csv",
    "EURUSD-OTC": "eurusd_otc_m1.csv",
    "GBPUSD-OTC": "gbpusd_otc_m1.csv",
    "USDJPY-OTC": "usdjpy_otc_m1.csv",
}


def main() -> None:
    summaries = []

    for symbol, filename in SYMBOL_FILES.items():
        csv_path = DATA_DIR / filename

        if not csv_path.exists():
            print(f"Pulando {symbol}: arquivo nao encontrado em {csv_path}")
            continue

        summary = CsvBacktester(str(csv_path), symbol).run(lookahead_candles=1)
        summaries.append(summary.to_dict())
        print(f"Backtest concluido para {symbol}: {summary.accuracy:.2%} de acerto")

    if not summaries:
        print("Nenhum backtest executado. Gere os dados com: python -m src.tools.generate_sample_data")
        return

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Relatorio salvo em {REPORT_PATH}")


if __name__ == "__main__":
    main()
