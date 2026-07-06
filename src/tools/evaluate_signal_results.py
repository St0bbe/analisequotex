from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


SIGNALS_PATH = Path("signals.csv")
OUTPUT_PATH = Path("signal_results.csv")
MAX_PRICE_DISTANCE_RATIO = 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avalia sinais BUY/SELL contra a vela seguinte disponivel")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forca avaliacao mesmo quando o preco do sinal parece incompatível com o CSV de candles.",
    )
    return parser.parse_args()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_candles(symbol: str) -> list[dict]:
    path = Path("data") / f"{symbol.lower().replace('-', '_')}_m1.csv"

    if not path.exists():
        return []

    candles: list[dict] = []
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            candles.append(
                {
                    "timestamp": parse_datetime(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )

    return candles


def normalize_time(candle_time: datetime, signal_time: datetime) -> datetime:
    if candle_time.tzinfo is not None and signal_time.tzinfo is None:
        return candle_time.replace(tzinfo=None)
    return candle_time


def find_reference_candle(candles: list[dict], signal_time: datetime) -> dict | None:
    previous = None
    for candle in candles:
        candle_time = normalize_time(candle["timestamp"], signal_time)
        if candle_time <= signal_time:
            previous = candle
        else:
            return previous
    return previous


def find_next_candle(candles: list[dict], signal_time: datetime) -> dict | None:
    for candle in candles:
        candle_time = normalize_time(candle["timestamp"], signal_time)
        if candle_time > signal_time:
            return candle

    return None


def is_price_compatible(signal_price: float, reference_price: float) -> bool:
    if reference_price == 0:
        return False
    distance = abs(signal_price - reference_price) / abs(reference_price)
    return distance <= MAX_PRICE_DISTANCE_RATIO


def evaluate_result(side: str, entry_price: float, candle: dict) -> str:
    close_price = candle["close"]

    if side == "BUY":
        if close_price > entry_price:
            return "WIN"
        if close_price < entry_price:
            return "LOSS"
        return "DRAW"

    if side == "SELL":
        if close_price < entry_price:
            return "WIN"
        if close_price > entry_price:
            return "LOSS"
        return "DRAW"

    return "IGNORED"


def main() -> None:
    args = parse_args()

    if not SIGNALS_PATH.exists():
        print("signals.csv nao encontrado. Rode o runner antes.")
        return

    rows = []
    candles_cache: dict[str, list[dict]] = {}

    with SIGNALS_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for signal in reader:
            side = signal["side"]
            if side == "WAIT":
                continue

            symbol = signal["symbol"]
            candles_cache.setdefault(symbol, load_candles(symbol))
            candles = candles_cache[symbol]

            if not candles:
                rows.append(
                    {
                        **signal,
                        "result": "NO_CANDLES",
                        "exit_time": "",
                        "exit_close": "",
                        "note": "arquivo de candles nao encontrado",
                    }
                )
                continue

            signal_time = parse_datetime(signal["created_at"])
            signal_price = float(signal["price"])
            reference_candle = find_reference_candle(candles, signal_time)
            next_candle = find_next_candle(candles, signal_time)

            if next_candle is None:
                rows.append(
                    {
                        **signal,
                        "result": "PENDING",
                        "exit_time": "",
                        "exit_close": "",
                        "note": "ainda nao ha candle posterior ao sinal no arquivo",
                    }
                )
                continue

            if reference_candle and not args.force:
                reference_price = float(reference_candle["close"])
                if not is_price_compatible(signal_price, reference_price):
                    rows.append(
                        {
                            **signal,
                            "result": "INCOMPATIBLE_DATA",
                            "exit_time": next_candle["timestamp"].isoformat(),
                            "exit_close": next_candle["close"],
                            "note": "preco do sinal distante do CSV; provavel mistura de sessoes/fontes",
                        }
                    )
                    continue

            result = evaluate_result(side, signal_price, next_candle)
            rows.append(
                {
                    **signal,
                    "result": result,
                    "exit_time": next_candle["timestamp"].isoformat(),
                    "exit_close": next_candle["close"],
                    "note": "avaliado",
                }
            )

    if not rows:
        print("Nenhum sinal BUY/SELL encontrado para avaliar.")
        return

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    totals: dict[str, int] = {
        "WIN": 0,
        "LOSS": 0,
        "DRAW": 0,
        "PENDING": 0,
        "NO_CANDLES": 0,
        "INCOMPATIBLE_DATA": 0,
    }
    for row in rows:
        totals[row["result"]] = totals.get(row["result"], 0) + 1

    evaluated = totals.get("WIN", 0) + totals.get("LOSS", 0) + totals.get("DRAW", 0)
    win_rate = totals.get("WIN", 0) / evaluated if evaluated else 0

    print("Resultado dos sinais:")
    print(f"WIN: {totals.get('WIN', 0)}")
    print(f"LOSS: {totals.get('LOSS', 0)}")
    print(f"DRAW: {totals.get('DRAW', 0)}")
    print(f"PENDING: {totals.get('PENDING', 0)}")
    print(f"NO_CANDLES: {totals.get('NO_CANDLES', 0)}")
    print(f"INCOMPATIBLE_DATA: {totals.get('INCOMPATIBLE_DATA', 0)}")
    print(f"Win rate avaliado: {win_rate:.2%}")
    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: se aparecer INCOMPATIBLE_DATA, o sinal e o CSV provavelmente nao vieram da mesma sessao/fonte.")


if __name__ == "__main__":
    main()
