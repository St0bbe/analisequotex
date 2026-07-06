from __future__ import annotations

import csv
from pathlib import Path


SIGNALS_SUMMARY_PATH = Path("signals_summary.csv")
BACKTEST_REPORT_PATH = Path("backtest_report.csv")
OUTPUT_PATH = Path("asset_ranking_report.csv")


def read_csv_by_symbol(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {row["symbol"]: row for row in reader}


def classify_asset(accuracy: float, actionable_rate: float, max_loss_streak: int) -> str:
    if accuracy >= 0.55 and actionable_rate >= 0.20 and max_loss_streak <= 5:
        return "FORTE"

    if accuracy >= 0.52 and actionable_rate >= 0.10:
        return "OBSERVACAO"

    return "CONSERVADOR"


def main() -> None:
    signals_summary = read_csv_by_symbol(SIGNALS_SUMMARY_PATH)
    backtest_summary = read_csv_by_symbol(BACKTEST_REPORT_PATH)

    if not signals_summary:
        print("signals_summary.csv nao encontrado. Rode: python -m src.tools.analyze_signals")
        return

    if not backtest_summary:
        print("backtest_report.csv nao encontrado. Rode: python -m src.tools.run_backtest_report")
        return

    rows: list[dict] = []

    for symbol, signal_row in signals_summary.items():
        backtest_row = backtest_summary.get(symbol)

        if not backtest_row:
            continue

        accuracy = float(backtest_row["accuracy"])
        actionable_rate = float(signal_row["actionable_rate"])
        max_loss_streak = int(backtest_row["max_loss_streak"])
        avg_confidence = float(signal_row["avg_confidence"])
        total_signals = int(backtest_row["total_signals"])

        classification = classify_asset(accuracy, actionable_rate, max_loss_streak)
        score = (accuracy * 0.60) + (actionable_rate * 0.25) + (avg_confidence * 0.15)

        rows.append(
            {
                "symbol": symbol,
                "classification": classification,
                "score": round(score, 4),
                "accuracy": accuracy,
                "actionable_rate": actionable_rate,
                "avg_confidence": avg_confidence,
                "max_loss_streak": max_loss_streak,
                "backtest_signals": total_signals,
                "runner_total": signal_row["total"],
                "runner_buy": signal_row["buy"],
                "runner_sell": signal_row["sell"],
                "runner_wait": signal_row["wait"],
            }
        )

    rows.sort(key=lambda row: row["score"], reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Ranking operacional dos ativos:")
    for row in rows:
        print(
            f"{row['symbol']} | {row['classification']} | "
            f"score {row['score']:.4f} | acerto {row['accuracy']:.2%} | "
            f"acionaveis {row['actionable_rate']:.2%}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
