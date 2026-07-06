from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


DEFAULT_RESULTS_PATH = Path("paper_validation_results.csv")
FALLBACK_RESULTS_PATH = Path("signal_results.csv")
OUTPUT_PATH = Path("real_performance_report.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera performance por ativo e direcao")
    parser.add_argument(
        "--input",
        default=None,
        help="Arquivo de resultados. Padrao: paper_validation_results.csv; fallback: signal_results.csv",
    )
    return parser.parse_args()


def resolve_input_path(value: str | None) -> Path | None:
    if value:
        path = Path(value)
        return path if path.exists() else None

    if DEFAULT_RESULTS_PATH.exists():
        return DEFAULT_RESULTS_PATH

    if FALLBACK_RESULTS_PATH.exists():
        return FALLBACK_RESULTS_PATH

    return None


def main() -> None:
    args = parse_args()
    input_path = resolve_input_path(args.input)

    if input_path is None:
        print("Nenhum arquivo de resultados encontrado.")
        print("Rode: python src/paper_validation_runner.py --feed simulated --cycles 3 --fresh")
        return

    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    with input_path.open("r", encoding="utf-8") as file:
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
                "source_file": str(input_path),
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

    print(f"Fonte analisada: {input_path}")
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
