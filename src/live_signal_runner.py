from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import get_settings
from src.data.csv_feed import CsvCandleFeed
from src.data.oanda_feed import OandaCandleFeed
from src.data.simulated_feed import SimulatedCandleFeed
from src.entry_window import CandleWindow
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger
from src.win_rate import estimated_win_rate_for, load_estimated_win_rates, passes_min_win_rate


console = Console()
SIGNALS_PATH = Path("signals.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Runner continuo de sinais M1")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Ativos para analisar. Exemplo: --symbols GBPUSD-OTC EURUSD-OTC",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Quantidade de ciclos M1 para executar. Exemplo: --cycles 5",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Limpa o signals.csv antes de iniciar a sessao.",
    )
    parser.add_argument(
        "--min-win-rate",
        type=float,
        default=53.0,
        help="Taxa minima estimada de win para destacar entrada. Exemplo: --min-win-rate 55",
    )
    parser.add_argument(
        "--feed",
        choices=["simulated", "csv", "oanda"],
        default="simulated",
        help="Fonte de candles: simulated, csv ou oanda.",
    )
    return parser.parse_args()


def build_candle_feed(feed_name: str):
    if feed_name == "csv":
        return CsvCandleFeed()

    if feed_name == "oanda":
        return OandaCandleFeed()

    return SimulatedCandleFeed()


def reset_signals_file() -> None:
    if SIGNALS_PATH.exists():
        SIGNALS_PATH.unlink()
        console.print("Historico signals.csv limpo para nova sessao.")


def render_signals(signals, cycle_number: int, win_rates: dict[str, float]) -> None:
    table = Table(title=f"Ciclo {cycle_number} - Sinais na janela ideal M1")
    table.add_column("Ativo")
    table.add_column("Alerta")
    table.add_column("Confianca")
    table.add_column("Win estimado")
    table.add_column("Preco")
    table.add_column("Motivo")

    for signal in signals:
        estimated = estimated_win_rate_for(signal.symbol, win_rates)
        estimated_label = f"{estimated:.2f}%" if estimated is not None else "sem relatorio"

        table.add_row(
            signal.symbol,
            signal.side.value,
            f"{signal.confidence:.2f}",
            estimated_label,
            f"{signal.price:.5f}",
            signal.reason,
        )

    console.print(table)


def render_actionable_alert(
    signals,
    seconds_to_next_candle: int,
    win_rates: dict[str, float],
    min_win_rate: float,
) -> None:
    actionable = [
        signal
        for signal in signals
        if signal.side.value != "WAIT" and passes_min_win_rate(signal.symbol, win_rates, min_win_rate)
    ]

    blocked = [
        signal
        for signal in signals
        if signal.side.value != "WAIT" and not passes_min_win_rate(signal.symbol, win_rates, min_win_rate)
    ]

    if not actionable:
        message = "Nenhum sinal acionavel nesta vela. Melhor aguardar."

        if blocked:
            blocked_lines = []
            for signal in blocked:
                estimated = estimated_win_rate_for(signal.symbol, win_rates)
                blocked_lines.append(
                    f"{signal.symbol} -> {signal.side.value} bloqueado | "
                    f"win estimado {estimated:.2f}% abaixo do minimo {min_win_rate:.2f}%"
                )
            message += "\n\n" + "\n".join(blocked_lines)

        console.print(Panel(message, title="SEM ENTRADA"))
        return

    print("\a", end="")

    lines = []
    for signal in actionable:
        estimated = estimated_win_rate_for(signal.symbol, win_rates)
        estimated_label = f"{estimated:.2f}%" if estimated is not None else "sem relatorio"
        lines.append(
            f"{signal.symbol} -> {signal.side.value} | "
            f"confianca {signal.confidence:.2f} | "
            f"win estimado {estimated_label} | "
            f"entrada na proxima vela em ~{seconds_to_next_candle}s"
        )

    console.print(
        Panel(
            "\n".join(lines),
            title="ALERTA OPERACIONAL",
            subtitle="Sinal apenas para estudo/simulacao. Nenhuma ordem real foi enviada.",
        )
    )


def wait_until_window(window: CandleWindow) -> None:
    last_bucket = None

    while not window.is_valid_analysis_time():
        seconds_to_next = window.seconds_to_next_candle()
        elapsed = window.elapsed_seconds()

        if elapsed > window.end_second:
            bucket = "next"
            message = f"Proxima vela em {seconds_to_next}s. Aguardando nova vela..."
        else:
            seconds_to_window = max(window.start_second - elapsed, 0)
            bucket = seconds_to_window // 5
            message = f"Aguardando janela ideal. Falta cerca de {seconds_to_window}s para analisar."

        if bucket != last_bucket or seconds_to_next <= 5:
            console.print(message)
            last_bucket = bucket

        time.sleep(1)


def wait_next_candle(window: CandleWindow) -> None:
    while window.is_valid_analysis_time():
        time.sleep(1)

    while window.seconds_to_next_candle() > 55:
        time.sleep(1)


def should_continue(cycle_number: int, max_cycles: int | None) -> bool:
    if max_cycles is None:
        return True

    return cycle_number <= max_cycles


def main() -> None:
    args = parse_args()

    if args.fresh:
        reset_signals_file()

    settings = get_settings()
    candle_feed = build_candle_feed(args.feed)
    scanner = MultiAssetScanner(settings, candle_feed=candle_feed)
    logger = SignalLogger()
    window = CandleWindow()
    win_rates = load_estimated_win_rates()
    selected_symbols = tuple(args.symbols) if args.symbols else settings.priority_symbols

    console.print("Runner continuo iniciado em modo de simulacao/analise.")
    console.print("Pressione CTRL+C para parar.")
    console.print(f"Fonte de candles: {args.feed}")
    console.print(f"Ativos selecionados: {', '.join(selected_symbols)}")
    console.print(f"Filtro de win estimado minimo: {args.min_win_rate:.2f}%")

    if not win_rates:
        console.print("Aviso: win_rate_estimate.csv nao encontrado. Rode python -m src.tools.run_full_analysis para gerar o relatorio.")

    if args.cycles:
        console.print(f"Ciclos configurados: {args.cycles}")

    cycle_number = 1

    try:
        while should_continue(cycle_number, args.cycles):
            console.print(f"\nAguardando janela ideal para o ciclo {cycle_number}...")
            wait_until_window(window)

            console.print(window.status_message())
            result = scanner.scan_symbols(selected_symbols)
            logger.append_many(result.signals)

            seconds_to_next_candle = window.seconds_to_next_candle()
            render_signals(result.ranked, cycle_number, win_rates)
            render_actionable_alert(result.ranked, seconds_to_next_candle, win_rates, args.min_win_rate)

            console.print(f"Segundos ate a proxima vela: {seconds_to_next_candle}")
            console.print(f"Sinais brutos BUY/SELL encontrados: {len(result.actionable)}")
            console.print("Nenhuma ordem real foi enviada.")

            cycle_number += 1
            if should_continue(cycle_number, args.cycles):
                wait_next_candle(window)

        console.print("\nRunner finalizado apos atingir a quantidade de ciclos configurada.")

    except KeyboardInterrupt:
        console.print("\nRunner continuo encerrado pelo usuario.")


if __name__ == "__main__":
    main()
