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
from src.entry_window import CandleWindow
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger


console = Console()


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
    return parser.parse_args()


def render_signals(signals, cycle_number: int) -> None:
    table = Table(title=f"Ciclo {cycle_number} - Sinais na janela ideal M1")
    table.add_column("Ativo")
    table.add_column("Alerta")
    table.add_column("Confianca")
    table.add_column("Preco")
    table.add_column("Motivo")

    for signal in signals:
        table.add_row(
            signal.symbol,
            signal.side.value,
            f"{signal.confidence:.2f}",
            f"{signal.price:.5f}",
            signal.reason,
        )

    console.print(table)


def render_actionable_alert(signals, seconds_to_next_candle: int) -> None:
    actionable = [signal for signal in signals if signal.side.value != "WAIT"]

    if not actionable:
        console.print(Panel("Nenhum sinal acionavel nesta vela. Melhor aguardar.", title="SEM ENTRADA"))
        return

    print("\a", end="")

    lines = []
    for signal in actionable:
        lines.append(
            f"{signal.symbol} -> {signal.side.value} | "
            f"confianca {signal.confidence:.2f} | "
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
    settings = get_settings()
    scanner = MultiAssetScanner(settings)
    logger = SignalLogger()
    window = CandleWindow()
    selected_symbols = tuple(args.symbols) if args.symbols else settings.priority_symbols

    console.print("Runner continuo iniciado em modo de simulacao.")
    console.print("Pressione CTRL+C para parar.")
    console.print(f"Ativos selecionados: {', '.join(selected_symbols)}")

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
            render_signals(result.ranked, cycle_number)
            render_actionable_alert(result.ranked, seconds_to_next_candle)

            console.print(f"Segundos ate a proxima vela: {seconds_to_next_candle}")
            console.print(f"Sinais acionaveis encontrados: {len(result.actionable)}")
            console.print("Nenhuma ordem real foi enviada.")

            cycle_number += 1
            if should_continue(cycle_number, args.cycles):
                wait_next_candle(window)

        console.print("\nRunner finalizado apos atingir a quantidade de ciclos configurada.")

    except KeyboardInterrupt:
        console.print("\nRunner continuo encerrado pelo usuario.")


if __name__ == "__main__":
    main()
