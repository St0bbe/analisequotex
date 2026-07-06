from __future__ import annotations

from src.entry_window import CandleWindow


def main() -> None:
    window = CandleWindow()

    print(window.status_message())
    print(f"Pode analisar agora: {'SIM' if window.is_valid_analysis_time() else 'NAO'}")
    print(f"Segundos ate a proxima vela: {window.seconds_to_next_candle()}")


if __name__ == "__main__":
    main()
