from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


SIGNALS_PATH = Path("signals.csv")
REPORT_PATH = Path("signals_summary.csv")


def main() -> None:
    if not SIGNALS_PATH.exists():
        print("Arquivo signals.csv nao encontrado. Rode antes: python src/runner.py")
        return

    summary: dict[str, Counter] = defaultdict(Counter)
    confidence_sum: dict[str, float] = defaultdict(float)
    confidence_count: dict[str, int] = defaultdict(int)

    with SIGNALS_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            symbol = row["symbol"]
            side = row["side"]
            confidence = float(row["confidence"])

            summary[symbol][side] += 1
            summary[symbol]["TOTAL"] += 1
            confidence_sum[symbol] += confidence
            confidence_count[symbol] += 1

    rows = []
    for symbol, counter in sorted(summary.items()):
        total = counter["TOTAL"]
        buy = counter["BUY"]
        sell = counter["SELL"]
        wait = counter["WAIT"]
        actionable = buy + sell
        avg_confidence = confidence_sum[symbol] / confidence_count[symbol]

        rows.append(
            {
                "symbol": symbol,
                "total": total,
                "buy": buy,
                "sell": sell,
                "wait": wait,
                "actionable": actionable,
                "actionable_rate": round(actionable / total, 4) if total else 0,
                "avg_confidence": round(avg_confidence, 4),
            }
        )

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "symbol",
                "total",
                "buy",
                "sell",
                "wait",
                "actionable",
                "actionable_rate",
                "avg_confidence",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Resumo dos sinais:")
    for row in rows:
        print(
            f"{row['symbol']} | total {row['total']} | "
            f"BUY {row['buy']} | SELL {row['sell']} | WAIT {row['wait']} | "
            f"acionaveis {row['actionable_rate']:.2%}"
        )

    print(f"Relatorio salvo em {REPORT_PATH}")


if __name__ == "__main__":
    main()
