from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


RESULTS_PATH = Path("signal_results.csv")
OUTPUT_PATH = Path("real_performance_report.csv")


def main() -> None:
    if not RESULTS_PATH.exists():
        print("signal_results.csv nao encontrado. Rode: python -m src.tools.evaluate_signal_results")
        return

    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    with RESULTS_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            result = row["result"]
            if result not in {"WIN", "LOSS", "DRAW"}:
                continue

            symbol = row["symbol"]
            side = row["side"]
            key = (symbol, side)
            stats[key]["total"] += 1
            stats[key][result.lower()] += 1

    rows = []
    for (symbol, side), item in stats.items():
        total = item["total"]
        win = item["win"]
        loss = item["loss"]
        draw = item["draw"]
        win_rate = win / total if total else 0

        rows.append(
            {
                "symbol": symbol,
                "side": side,
                "total": total,
                "win": win,
                "loss": loss,
                "draw": draw,
                "win_rate": round(win_rate, 4),
            }
        )

    if not rows:
        print("Nenhum resultado avaliado encontrado.")
        return

    rows.sort(key=lambda row: (row["win_rate"], row["total"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Performance por ativo e direcao:")
    for row in rows:
        print(
            f"{row['symbol']} {row['side']} | "
            f"win rate {row['win_rate']:.2%} | "
            f"total {row['total']} | "
            f"WIN {row['win']} | LOSS {row['loss']} | DRAW {row['draw']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: em dados simulados, isso ainda nao representa performance real.")


if __name__ == "__main__":
    main()
