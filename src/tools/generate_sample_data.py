from __future__ import annotations

import csv
from pathlib import Path

from src.data.simulated_feed import SimulatedCandleFeed


OUTPUT_DIR = Path("data")


def generate_symbol_csv(symbol: str, initial_price: float, candles_count: int = 1000) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{symbol.lower().replace('-', '_')}_m1.csv"
    feed = SimulatedCandleFeed(initial_price=initial_price)
    candles = feed.get_recent_candles(symbol, candles_count)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "open", "high", "low", "close"])
        writer.writeheader()

        for candle in candles:
            writer.writerow(
                {
                    "timestamp": candle.timestamp.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                }
            )

    return output_path


def main() -> None:
    symbols = {
        "EURUSD": 1.1000,
        "GBPUSD": 1.2700,
        "USDJPY": 157.50,
        "EURUSD-OTC": 1.1000,
        "GBPUSD-OTC": 1.2700,
        "USDJPY-OTC": 157.50,
    }

    for symbol, price in symbols.items():
        output_path = generate_symbol_csv(symbol, price)
        print(f"Arquivo gerado: {output_path}")


if __name__ == "__main__":
    main()
