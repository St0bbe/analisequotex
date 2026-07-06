from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

from src.backtesting import CsvBacktester
from src.config import get_settings


DATA_DIR = Path("data")
REPORT_PATH = Path("confidence_optimization_report.csv")
BEST_REPORT_PATH = Path("best_confidence_report.csv")

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

    print("Iniciando otimizacao de confianca...")

    for confidence in CONFIDENCE_LEVELS:
        settings = replace(base_settings, min_confidence=confidence)
        print(f"Testando confianca {confidence:.2f}...")

        for symbol, filename in SYMBOL_FILES.items():
            csv_path = DATA_DIR / filename

            if not csv_path.exists():
                print(f"Pulando {symbol}: arquivo nao encontrado em {csv_path}")
                continue

            summary = CsvBacktester(str(csv_path), symbol, settings=settings).run(lookahead_candles=1)
            row = summary.to_dict()
            row["min_confidence"] = confidence
            rows.append(row)

    if not rows:
        print("Nenhum resultado gerado. Execute antes: python -m src.tools.generate_sample_data")
        return

    fieldnames = ["min_confidence"] + [key for key in rows[0].keys() if key != "min_confidence"]

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    best_rows = get_best_rows(rows)

    with BEST_REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(best_rows)

    print("\nMelhores configuracoes por ativo:")
    for row in best_rows:
        print(
            f"{row['symbol']} | confianca {row['min_confidence']:.2f} | "
            f"acerto {row['accuracy']:.2%} | sinais {row['total_signals']} | "
            f"max perdas seguidas {row['max_loss_streak']}"
        )

    print(f"\nRelatorio completo salvo em {REPORT_PATH}")
    print(f"Melhores configuracoes salvas em {BEST_REPORT_PATH}")


def get_best_rows(rows: list[dict]) -> list[dict]:
    best_by_symbol: dict[str, dict] = {}

    for row in rows:
        symbol = row["symbol"]
        current_best = best_by_symbol.get(symbol)

        if current_best is None:
            best_by_symbol[symbol] = row
            continue

        row_score = (row["accuracy"], row["total_signals"], -row["max_loss_streak"])
        best_score = (
            current_best["accuracy"],
            current_best["total_signals"],
            -current_best["max_loss_streak"],
        )

        if row_score > best_score:
            best_by_symbol[symbol] = row

    return list(best_by_symbol.values())


if __name__ == "__main__":
    main()
