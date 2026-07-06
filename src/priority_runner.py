from __future__ import annotations

import sys
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


def render_priority(signals) -> None:
    table = Table(title="Scanner prioritario - ativos com melhor desempenho")
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
    window = CandleWindow()

    console.print("Executando scanner prioritario em modo de simulacao.")
    console.print(f"Ativos priorizados: {', '.join(settings.priority_symbols)}")
    console.print(window.status_message())

    if not window.is_valid_analysis_time():
        console.print("Fora da janela ideal. Nenhum sinal sera gerado agora.")
        console.print("Rode novamente perto dos ultimos segundos da vela M1.")
        return

    result = scanner.scan_priority()
    logger.append_many(result.signals)
    render_priority(result.ranked)

    actionable = result.actionable
    console.print(f"\nSinais acionaveis encontrados: {len(actionable)}")
    console.print(f"Segundos ate a proxima vela: {window.seconds_to_next_candle()}")
    console.print("Nenhuma ordem real foi enviada.")


if __name__ == "__main__":
    main()
