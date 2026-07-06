from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


INPUT_PATH = Path("csv_replay_results.csv")
OUTPUT_PATH = Path("csv_replay_opportunity_report.csv")


def inverted_result(result: str) -> str:
    if result == "WIN":
        return "LOSS"
    if result == "LOSS":
        return "WIN"
    return result


def rate(win: int, total: int) -> float:
    return win / total if total else 0.0


def label(total: int, normal_rate: float, inverse_rate: float) -> str:
    if total < 30:
        return "POUCOS_DADOS"
    if normal_rate >= 0.55:
        return "NORMAL_PROMISSOR"
    if inverse_rate >= 0.55:
        return "INVERSAO_PROMISSORA"
    if normal_rate < 0.50 and inverse_rate < 0.50:
        return "EVITAR"
    return "OBSERVAR"


def main() -> None:
    if not INPUT_PATH.exists():
        print("csv_replay_results.csv nao encontrado.")
        print("Rode antes: python -m src.tools.run_csv_replay --include-all-signals --fresh")
        return

    stats = defaultdict(
        lambda: {
            "total": 0,
            "win": 0,
            "loss": 0,
            "draw": 0,
            "inverse_win": 0,
            "inverse_loss": 0,
            "inverse_draw": 0,
        }
    )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            result = row["result"]
            if result not in {"WIN", "LOSS", "DRAW"}:
                continue

            key = (row["symbol"], row["side"], row.get("filter_status", "UNKNOWN"))
            inv = inverted_result(result)

            stats[key]["total"] += 1
            stats[key][result.lower()] += 1
            stats[key][f"inverse_{inv.lower()}"] += 1

    rows = []
    for (symbol, side, filter_status), item in stats.items():
        total = item["total"]
        normal_win_rate = rate(item["win"], total)
        inverse_win_rate = rate(item["inverse_win"], total)
        recommendation = label(total, normal_win_rate, inverse_win_rate)

        rows.append(
            {
                "symbol": symbol,
                "side": side,
                "filter_status": filter_status,
                "total": total,
                "normal_win": item["win"],
                "normal_loss": item["loss"],
                "normal_draw": item["draw"],
                "normal_win_rate_percent": round(normal_win_rate * 100, 2),
                "inverse_win": item["inverse_win"],
                "inverse_loss": item["inverse_loss"],
                "inverse_draw": item["inverse_draw"],
                "inverse_win_rate_percent": round(inverse_win_rate * 100, 2),
                "recommendation": recommendation,
            }
        )

    if not rows:
        print("Nenhum resultado valido encontrado.")
        return

    rows.sort(
        key=lambda row: (
            row["recommendation"] == "NORMAL_PROMISSOR",
            row["recommendation"] == "INVERSAO_PROMISSORA",
            max(row["normal_win_rate_percent"], row["inverse_win_rate_percent"]),
            row["total"],
        ),
        reverse=True,
    )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Analise de oportunidades do replay:")
    for row in rows[:20]:
        print(
            f"{row['symbol']} {row['side']} {row['filter_status']} | "
            f"normal {row['normal_win_rate_percent']}% | "
            f"invertido {row['inverse_win_rate_percent']}% | "
            f"total {row['total']} | {row['recommendation']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: inversao promissora exige validacao em dados reais antes de qualquer uso pratico.")


if __name__ == "__main__":
    main()
