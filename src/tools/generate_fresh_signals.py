from __future__ import annotations

from pathlib import Path

from src.config import get_settings
from src.scanner import MultiAssetScanner
from src.storage.signal_logger import SignalLogger


SIGNALS_PATH = Path("signals.csv")


def main() -> None:
    if SIGNALS_PATH.exists():
        SIGNALS_PATH.unlink()

    settings = get_settings()
    scanner = MultiAssetScanner(settings)
    logger = SignalLogger()

    print(f"Gerando sinais frescos em {settings.scanner_cycles} ciclos...")

    for cycle_number in range(1, settings.scanner_cycles + 1):
        result = scanner.scan_once()
        logger.append_many(result.signals)
        actionable = len(result.actionable)
        print(f"Ciclo {cycle_number}: {actionable} sinais acionaveis")

    print("signals.csv atualizado com sinais frescos.")


if __name__ == "__main__":
    main()
