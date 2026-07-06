from __future__ import annotations

import csv
from pathlib import Path


WIN_RATE_PATH = Path("win_rate_estimate.csv")
EMPIRICAL_WIN_RATE_PATH = Path("empirical_win_rates.csv")
MIN_EMPIRICAL_SAMPLES = 10


def load_estimated_win_rates(path: Path = WIN_RATE_PATH) -> dict[str, float]:
    if not path.exists():
        return {}

    rates: dict[str, float] = {}

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            symbol = row.get("symbol")
            value = row.get("estimated_win_rate_percent")

            if not symbol or not value:
                continue

            rates[symbol] = float(value)

    return rates


def load_empirical_win_rates(path: Path = EMPIRICAL_WIN_RATE_PATH) -> dict[str, float]:
    if not path.exists():
        return {}

    rates: dict[str, float] = {}

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            symbol = row.get("symbol")
            value = row.get("empirical_win_rate_percent")
            total = int(row.get("total", "0") or 0)

            if not symbol or not value or total < MIN_EMPIRICAL_SAMPLES:
                continue

            rates[symbol] = float(value)

    return rates


def load_combined_win_rates() -> dict[str, float]:
    rates = load_estimated_win_rates()
    empirical_rates = load_empirical_win_rates()
    rates.update(empirical_rates)
    return rates


def estimated_win_rate_for(symbol: str, rates: dict[str, float]) -> float | None:
    return rates.get(symbol)


def passes_min_win_rate(symbol: str, rates: dict[str, float], min_win_rate: float) -> bool:
    estimated = estimated_win_rate_for(symbol, rates)

    if estimated is None:
        return True

    return estimated >= min_win_rate
