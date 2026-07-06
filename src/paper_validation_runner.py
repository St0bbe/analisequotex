from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import UTC, datetime
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
from src.win_rate import passes_min_win_rate, load_combined_win_rates, estimated_win_rate_for


console = Console()
OUTPUT_PATH = Path("paper_validation_results.csv")
OPPORTUNITY_PATH = Path("csv_replay_opportunity_report.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validacao em papel de sinais M1")
    parser.add_argument("--symbols", nargs="+", help="Ativos para analisar")
    parser.add_argument("--cycles", type=int, default=3, help="Quantidade de ciclos para validar")
    parser.add_argument("--min-win-rate", type=float, default=53.0, help="Filtro minimo de taxa combinada")
    parser.add_argument("--feed", choices=["simulated", "csv", "oanda"], default="simulated")
    parser.add_argument("--fresh", action="store_true", help="Limpa o relatorio anterior")
    parser.add_argument(
        "--include-all-signals",
        action="store_true",
        help="Valida todos os sinais BUY/SELL, mesmo abaixo do filtro de win combinado.",
    )
    parser.add_argument(
        "--direction-mode",
        choices=["normal", "inverted", "auto"],
        default="normal",
        help="Modo de direcao: normal, inverted ou auto com base no relatorio de oportunidades.",
    )
    return parser.parse_args()


def build_feed(name: str):
    if name == "csv":
        return CsvCandleFeed()
    if name == "oanda":
        return OandaCandleFeed()
    return SimulatedCandleFeed()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def opposite_side(side: str) -> str:
    if side == "BUY":
        return "SELL"
    if side == "SELL":
        return "BUY"
    return side


def load_auto_inversion_map(path: Path = OPPORTUNITY_PATH) -> set[tuple[str, str]]:
    if not path.exists():
        return set()

    items: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("recommendation") != "INVERSAO_PROMISSORA":
                continue
            items.add((row["symbol"], row["side"]))

    return items


def should_invert(symbol: str, side: str, direction_mode: str, opportunity_map: set[tuple[str, str]]) -> bool:
    if direction_mode == "inverted":
        return True
    if direction_mode == "auto":
        return (symbol, side) in opportunity_map
    return False


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
        "original_side",
        "effective_side",
        "confidence",
        "combined_win_rate",
        "entry_price",
        "exit_price",
        "result",
        "filter_status",
        "direction_mode",
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
    table.add_column("Original")
    table.add_column("Final")
    table.add_column("Direcao")
    table.add_column("Filtro")
    table.add_column("Resultado")

    for row in rows:
        table.add_row(
            row["symbol"],
            row["original_side"],
            row["effective_side"],
            row["direction_mode"],
            row["filter_status"],
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
    win_rates = load_combined_win_rates()
    inversion_map = load_auto_inversion_map() if args.direction_mode == "auto" else set()
    symbols = tuple(args.symbols) if args.symbols else settings.priority_symbols

    console.print("Validacao em papel iniciada.")
    console.print(f"Fonte de candles: {args.feed}")
    console.print(f"Ativos: {', '.join(symbols)}")
    console.print(f"Ciclos: {args.cycles}")
    console.print(f"Modo de direcao: {args.direction_mode}")
    if args.direction_mode == "auto":
        console.print(f"Regras de inversao carregadas: {len(inversion_map)}")
    console.print("Taxa usada no filtro: combinada (empirica confiavel substitui estimada).")
    if args.include_all_signals:
        console.print("Modo coleta: validando todos os sinais BUY/SELL para aumentar amostras.")

    for cycle in range(1, args.cycles + 1):
        console.print(f"\nAguardando janela do ciclo {cycle}...")
        wait_until_window(window)
        result = scanner.scan_symbols(symbols)

        selected = []
        for signal in result.ranked:
            if signal.side.value == "WAIT":
                continue

            passed_filter = passes_min_win_rate(signal.symbol, win_rates, args.min_win_rate)
            if args.include_all_signals or passed_filter:
                selected.append((signal, "PASSED" if passed_filter else "BELOW_FILTER"))

        if not selected:
            console.print("Nenhum sinal passou nos filtros deste ciclo.")
            wait_next_closed_candle(window)
            continue

        console.print("Aguardando fechamento da vela seguinte para validar...")
        wait_next_closed_candle(window)

        rows = []
        for signal, filter_status in selected:
            candles = feed.get_recent_candles(signal.symbol, settings.candle_limit)
            if not candles:
                continue
            exit_price = candles[-1].close
            combined = estimated_win_rate_for(signal.symbol, win_rates)
            original_side = signal.side.value
            inverted = should_invert(signal.symbol, original_side, args.direction_mode, inversion_map)
            effective_side = opposite_side(original_side) if inverted else original_side
            applied_direction = "inverted" if inverted else "normal"
            rows.append(
                {
                    "created_at": signal.created_at.isoformat(),
                    "evaluated_at": utc_now_iso(),
                    "feed": args.feed,
                    "symbol": signal.symbol,
                    "original_side": original_side,
                    "effective_side": effective_side,
                    "confidence": signal.confidence,
                    "combined_win_rate": combined if combined is not None else "",
                    "entry_price": signal.price,
                    "exit_price": exit_price,
                    "result": evaluate(effective_side, signal.price, exit_price),
                    "filter_status": filter_status,
                    "direction_mode": applied_direction,
                    "reason": signal.reason,
                }
            )

        append_rows(rows)
        render_rows(rows)

    console.print(f"\nRelatorio salvo em {OUTPUT_PATH}")
    console.print("Aviso: use feed real para medir desempenho real; simulated serve apenas para testar o fluxo.")


if __name__ == "__main__":
    main()
