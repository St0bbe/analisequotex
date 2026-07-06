from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


DEFAULT_INPUT_PATH = Path("paper_validation_results.csv")
OUTPUT_PATH = Path("empirical_win_rates.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera win rate empirico a partir das validacoes em papel")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH), help="Arquivo de validacoes")
    parser.add_argument("--min-samples", type=int, default=10, help="Minimo de amostras para considerar confiavel")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Arquivo nao encontrado: {input_path}")
        print("Rode antes: python src/paper_validation_runner.py --feed simulated --cycles 10 --fresh")
        return

    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    with input_path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            result = row["result"]
            if result not in {"WIN", "LOSS", "DRAW"}:
                continue

            symbol = row["symbol"]
            stats[symbol]["total"] += 1
            stats[symbol][result.lower()] += 1

    rows = []
    for symbol, item in stats.items():
        total = item["total"]
        win = item["win"]
        loss = item["loss"]
        draw = item["draw"]
        evaluated = win + loss + draw
        win_rate = win / evaluated if evaluated else 0
        confidence_label = "CONFIAVEL" if evaluated >= args.min_samples else "POUCOS_DADOS"

        rows.append(
            {
                "symbol": symbol,
                "empirical_win_rate_percent": round(win_rate * 100, 2),
                "total": total,
                "win": win,
                "loss": loss,
                "draw": draw,
                "sample_status": confidence_label,
                "source_file": str(input_path),
            }
        )

    if not rows:
        print("Nenhum resultado WIN/LOSS/DRAW encontrado para calcular win rate empirico.")
        return

    rows.sort(key=lambda row: (row["sample_status"] == "CONFIAVEL", row["empirical_win_rate_percent"], row["total"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Win rate empirico por ativo:")
    for row in rows:
        print(
            f"{row['symbol']} | empirico {row['empirical_win_rate_percent']}% | "
            f"total {row['total']} | WIN {row['win']} | LOSS {row['loss']} | "
            f"status {row['sample_status']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: poucos dados nao devem ser usados para conclusao operacional.")


if __name__ == "__main__":
    main()
