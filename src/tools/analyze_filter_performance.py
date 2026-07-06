from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


INPUT_PATH = Path("paper_validation_results.csv")
OUTPUT_PATH = Path("filter_performance_report.csv")


def main() -> None:
    if not INPUT_PATH.exists():
        print("paper_validation_results.csv nao encontrado.")
        print("Rode: .\\scripts\\run_paper_validation.ps1 -Feed simulated -Cycles 30 -IncludeAllSignals")
        return

    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            result = row["result"]
            if result not in {"WIN", "LOSS", "DRAW"}:
                continue

            symbol = row["symbol"]
            side = row["side"]
            filter_status = row.get("filter_status", "UNKNOWN")
            key = (symbol, side, filter_status)

            stats[key]["total"] += 1
            stats[key][result.lower()] += 1

    rows = []
    for (symbol, side, filter_status), item in stats.items():
        total = item["total"]
        win = item["win"]
        loss = item["loss"]
        draw = item["draw"]
        win_rate = win / total if total else 0

        rows.append(
            {
                "symbol": symbol,
                "side": side,
                "filter_status": filter_status,
                "total": total,
                "win": win,
                "loss": loss,
                "draw": draw,
                "win_rate_percent": round(win_rate * 100, 2),
            }
        )

    if not rows:
        print("Nenhuma linha avaliada encontrada.")
        return

    rows.sort(key=lambda row: (row["win_rate_percent"], row["total"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Performance por status do filtro:")
    for row in rows:
        print(
            f"{row['symbol']} {row['side']} {row['filter_status']} | "
            f"win rate {row['win_rate_percent']}% | "
            f"total {row['total']} | WIN {row['win']} | LOSS {row['loss']} | DRAW {row['draw']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: use feed real para validar conclusoes reais.")


if __name__ == "__main__":
    main()
