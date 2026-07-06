from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

from src.config import get_settings
from src.data.csv_feed import CsvCandleFeed
from src.data.oanda_feed import OandaCandleFeed
from src.data.simulated_feed import SimulatedCandleFeed
from src.entry_window import CandleWindow
from src.scanner import MultiAssetScanner
from src.win_rate import passes_min_win_rate, load_estimated_win_rates, estimated_win_rate_for


console = Console()
OUTPUT_PATH = Path("paper_validation_results.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validacao em papel de sinais M1")
    parser.add_argument("--symbols", nargs="+", help="Ativos para analisar")
    parser.add_argument("--cycles", type=int, default=3, help="Quantidade de ciclos para validar")
    parser.add_argument("--min-win-rate", type=float, default=53.0, help="Filtro minimo de taxa estimada")
    parser.add_argument("--feed", choices=["simulated", "csv", "oanda"], default="simulated")
    parser.add_argument("--fresh", action="store_true", help="Limpa o relatorio anterior")
    return parser.parse_args()


def build_feed(name: str):
    if name == "csv":
        return CsvCandleFeed()
    if name == "oanda":
        return OandaCandleFeed()
    return SimulatedCandleFeed()


def wait_until_window(window: CandleWindow) -> None:
    while not window.is_valid_analysis_time():
        time.sleep(1)


def wait_next_closed_candle(window: CandleWindow) -> None:
    while window.is_valid_analysis_time():
        time.sleep(1)
    while window.seconds_to_next_candle() > 55:
        time.sleep(1)
    time.sleep(2)


def evaluate(side: str, entry_price: float, exit_price: float) -> str:
    if side == "BUY":
        if exit_price > entry_price:
            return "WIN"
        if exit_price < entry_price:
            return "LOSS"
        return "DRAW"
    if side == "SELL":
        if exit_price < entry_price:
            return "WIN"
        if exit_price > entry_price:
            return "LOSS"
        return "DRAW"
    return "IGNORED"


def append_rows(rows: list[dict]) -> None:
    if not rows:
        return

    exists = OUTPUT_PATH.exists()
    fields = [
        "created_at",
        "evaluated_at",
        "feed",
        "symbol",
        "side",
        "confidence",
        "estimated_win_rate",
        "entry_price",
        "exit_price",
        "result",
        "reason",
    ]

    with OUTPUT_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def render_rows(rows: list[dict]) -> None:
    table = Table(title="Validacao da vela seguinte")
    table.add_column("Ativo")
    table.add_column("Lado")
    table.add_column("Entrada")
    table.add_column("Fechamento")
    table.add_column("Resultado")

    for row in rows:
        table.add_row(
            row["symbol"],
            row["side"],
            str(row["entry_price"]),
            str(row["exit_price"]),
            row["result"],
        )

    console.print(table)


def main() -> None:
    args = parse_args()

    if args.fresh and OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        console.print("Relatorio anterior limpo.")

    settings = get_settings()
    feed = build_feed(args.feed)
    scanner = MultiAssetScanner(settings, candle_feed=feed)
    window = CandleWindow()
    win_rates = load_estimated_win_rates()
    symbols = tuple(args.symbols) if args.symbols else settings.priority_symbols

    console.print("Validacao em papel iniciada.")
    console.print(f"Fonte de candles: {args.feed}")
    console.print(f"Ativos: {', '.join(symbols)}")
    console.print(f"Ciclos: {args.cycles}")

    for cycle in range(1, args.cycles + 1):
        console.print(f"\nAguardando janela do ciclo {cycle}...")
        wait_until_window(window)
        result = scanner.scan_symbols(symbols)

        selected = []
        for signal in result.ranked:
            if signal.side.value == "WAIT":
                continue
            if passes_min_win_rate(signal.symbol, win_rates, args.min_win_rate):
                selected.append(signal)

        if not selected:
            console.print("Nenhum sinal passou nos filtros deste ciclo.")
            wait_next_closed_candle(window)
            continue

        console.print("Aguardando fechamento da vela seguinte para validar...")
        wait_next_closed_candle(window)

        rows = []
        for signal in selected:
            candles = feed.get_recent_candles(signal.symbol, settings.candle_limit)
            if not candles:
                continue
            exit_price = candles[-1].close
            estimated = estimated_win_rate_for(signal.symbol, win_rates)
            rows.append(
                {
                    "created_at": signal.created_at.isoformat(),
                    "evaluated_at": datetime.utcnow().isoformat(),
                    "feed": args.feed,
                    "symbol": signal.symbol,
                    "side": signal.side.value,
                    "confidence": signal.confidence,
                    "estimated_win_rate": estimated if estimated is not None else "",
                    "entry_price": signal.price,
                    "exit_price": exit_price,
                    "result": evaluate(signal.side.value, signal.price, exit_price),
                    "reason": signal.reason,
                }
            )

        append_rows(rows)
        render_rows(rows)

    console.print(f"\nRelatorio salvo em {OUTPUT_PATH}")
    console.print("Aviso: use feed real para medir desempenho real; simulated serve apenas para testar o fluxo.")


if __name__ == "__main__":
    main()
