from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


SIGNALS_PATH = Path("signals.csv")
OUTPUT_PATH = Path("live_session_summary.csv")


def main() -> None:
    if not SIGNALS_PATH.exists():
        print("signals.csv nao encontrado. Rode antes: python src/live_signal_runner.py --cycles 10")
        return

    by_symbol: dict[str, Counter] = defaultdict(Counter)
    confidence_sum: dict[str, float] = defaultdict(float)
    confidence_count: dict[str, int] = defaultdict(int)
    total_rows = 0

    with SIGNALS_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            symbol = row["symbol"]
            side = row["side"]
            confidence = float(row["confidence"])

            by_symbol[symbol][side] += 1
            by_symbol[symbol]["TOTAL"] += 1
            confidence_sum[symbol] += confidence
            confidence_count[symbol] += 1
            total_rows += 1

    if not by_symbol:
        print("Nenhum sinal encontrado em signals.csv")
        return

    rows = []
    for symbol, counter in sorted(by_symbol.items()):
        total = counter["TOTAL"]
        buy = counter["BUY"]
        sell = counter["SELL"]
        wait = counter["WAIT"]
        actionable = buy + sell
        actionable_rate = actionable / total if total else 0
        avg_confidence = confidence_sum[symbol] / confidence_count[symbol]

        rows.append(
            {
                "symbol": symbol,
                "total": total,
                "buy": buy,
                "sell": sell,
                "wait": wait,
                "actionable": actionable,
                "actionable_rate": round(actionable_rate, 4),
                "avg_confidence": round(avg_confidence, 4),
            }
        )

    rows.sort(key=lambda row: (row["actionable"], row["avg_confidence"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Resumo da sessao ao vivo:")
    print(f"Total de registros analisados: {total_rows}")

    for row in rows:
        print(
            f"{row['symbol']} | total {row['total']} | "
            f"BUY {row['buy']} | SELL {row['sell']} | WAIT {row['wait']} | "
            f"acionaveis {row['actionable_rate']:.2%} | "
            f"confianca media {row['avg_confidence']:.2f}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
