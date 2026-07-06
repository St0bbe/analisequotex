from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

from src.config import get_settings
from src.entry_window import CandleWindow
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger


console = Console()


def render_signals(signals) -> None:
    table = Table(title="Sinal na janela ideal da vela M1")
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


def wait_until_window(window: CandleWindow) -> None:
    while not window.is_valid_analysis_time():
        console.print(window.status_message())
        time.sleep(1)


def main() -> None:
    settings = get_settings()
    scanner = MultiAssetScanner(settings)
    logger = SignalLogger()
    window = CandleWindow()

    console.print("Aguardando a janela ideal da vela M1...")
    console.print("O sinal sera gerado apenas perto da abertura da proxima vela.")

    wait_until_window(window)

    console.print(window.status_message())
    result = scanner.scan_priority()
    logger.append_many(result.signals)
    render_signals(result.ranked)

    console.print(f"\nSegundos ate a proxima vela: {window.seconds_to_next_candle()}")
    console.print(f"Sinais acionaveis encontrados: {len(result.actionable)}")
    console.print("Nenhuma ordem real foi enviada.")


if __name__ == "__main__":
    main()
