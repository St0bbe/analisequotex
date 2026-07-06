from __future__ import annotations

import csv
from pathlib import Path


BACKTEST_REPORT_PATH = Path("backtest_report.csv")
BEST_CONFIDENCE_PATH = Path("best_confidence_report.csv")
ASSET_RANKING_PATH = Path("asset_ranking_report.csv")
OUTPUT_PATH = Path("win_rate_estimate.csv")


def read_by_symbol(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return {row["symbol"]: row for row in csv.DictReader(file)}


def risk_label(win_rate: float, max_loss_streak: int) -> str:
    if win_rate >= 0.58 and max_loss_streak <= 5:
        return "MELHOR CENARIO SIMULADO"

    if win_rate >= 0.53 and max_loss_streak <= 6:
        return "ACEITAVEL EM SIMULACAO"

    return "FRACO OU INCONSISTENTE"


def main() -> None:
    backtest = read_by_symbol(BACKTEST_REPORT_PATH)
    best_confidence = read_by_symbol(BEST_CONFIDENCE_PATH)
    ranking = read_by_symbol(ASSET_RANKING_PATH)

    if not backtest:
        print("backtest_report.csv nao encontrado. Rode: python -m src.tools.run_backtest_report")
        return

    rows: list[dict] = []

    for symbol, row in backtest.items():
        accuracy = float(row["accuracy"])
        max_loss_streak = int(row["max_loss_streak"])
        total_signals = int(row["total_signals"])
        best_row = best_confidence.get(symbol, {})
        ranking_row = ranking.get(symbol, {})

        rows.append(
            {
                "symbol": symbol,
                "estimated_win_rate_percent": round(accuracy * 100, 2),
                "total_backtest_signals": total_signals,
                "max_loss_streak": max_loss_streak,
                "best_confidence": best_row.get("min_confidence", ""),
                "classification": ranking_row.get("classification", ""),
                "risk_label": risk_label(accuracy, max_loss_streak),
            }
        )

    rows.sort(key=lambda item: item["estimated_win_rate_percent"], reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Chance estimada de win por ativo, baseada apenas no backtest simulado:")
    for row in rows:
        print(
            f"{row['symbol']} | {row['estimated_win_rate_percent']:.2f}% | "
            f"sinais {row['total_backtest_signals']} | "
            f"perdas seguidas max {row['max_loss_streak']} | {row['risk_label']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: isso nao garante resultado real. Use apenas para estudo, simulacao e validacao estatistica.")


if __name__ == "__main__":
    main()
