from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

from src.config import get_settings
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger


console = Console()


def render_cycle(cycle_number: int, signals) -> None:
    table = Table(title=f"Ciclo {cycle_number} - Scanner M1")
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


def main() -> None:
    settings = get_settings()
    scanner = MultiAssetScanner(settings)
    logger = SignalLogger()

    console.print("Executando ciclos de simulacao. Nenhuma ordem real sera enviada.\n")

    for cycle_number in range(1, settings.scanner_cycles + 1):
        result = scanner.scan_once()
        logger.append_many(result.signals)
        render_cycle(cycle_number, result.ranked)

    console.print("\nSimulacao finalizada. Historico salvo em signals.csv")


if __name__ == "__main__":
    main()
