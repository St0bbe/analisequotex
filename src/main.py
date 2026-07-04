from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.config import get_settings
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger


console = Console()


def render_table(signals) -> None:
    table = Table(title="Scanner multiativo - simulacao M1")
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

    result = scanner.scan_once()
    logger.append_many(result.signals)
    render_table(result.ranked)

    console.print("\nResultado salvo em signals.csv")
    console.print("Este modo e apenas simulacao/estudo, sem ordens reais.")


if __name__ == "__main__":
    main()
