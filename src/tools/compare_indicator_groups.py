from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.indicators.technical import add_all_indicators


DATA_FILES = {
    "EURUSD": Path("data/eurusd_m1.csv"),
    "GBPUSD": Path("data/gbpusd_m1.csv"),
    "USDJPY": Path("data/usdjpy_m1.csv"),
    "EURUSD-OTC": Path("data/eurusd_otc_m1.csv"),
    "GBPUSD-OTC": Path("data/gbpusd_otc_m1.csv"),
    "USDJPY-OTC": Path("data/usdjpy_otc_m1.csv"),
}
OUTPUT_PATH = Path("indicator_group_report.csv")


def signal_trend(row: pd.Series) -> str:
    if row["fast_ma"] > row["slow_ma"] and row["close"] > row["ema_trend"]:
        return "BUY"
    if row["fast_ma"] < row["slow_ma"] and row["close"] < row["ema_trend"]:
        return "SELL"
    return "WAIT"


def signal_rsi(row: pd.Series) -> str:
    rsi = row["rsi"]
    if 48 <= rsi <= 66:
        return "BUY"
    if 34 <= rsi <= 52:
        return "SELL"
    return "WAIT"


def signal_macd(row: pd.Series, previous: pd.Series) -> str:
    if row["macd_histogram"] > previous["macd_histogram"]:
        return "BUY"
    if row["macd_histogram"] < previous["macd_histogram"]:
        return "SELL"
    return "WAIT"


def signal_stochastic(row: pd.Series) -> str:
    if row["stoch_k"] > row["stoch_d"] and 20 <= row["stoch_k"] <= 80:
        return "BUY"
    if row["stoch_k"] < row["stoch_d"] and 20 <= row["stoch_k"] <= 80:
        return "SELL"
    return "WAIT"


def signal_bollinger(row: pd.Series) -> str:
    if row["close"] > row["bb_middle"]:
        return "BUY"
    if row["close"] < row["bb_middle"]:
        return "SELL"
    return "WAIT"


def signal_candle(row: pd.Series) -> str:
    if bool(row["is_bullish_candle"]) and row["body_ratio"] >= 0.35:
        return "BUY"
    if bool(row["is_bearish_candle"]) and row["body_ratio"] >= 0.35:
        return "SELL"
    return "WAIT"


def next_candle_result(signal: str, current_close: float, next_close: float) -> bool | None:
    if signal == "BUY":
        return next_close > current_close
    if signal == "SELL":
        return next_close < current_close
    return None


def evaluate_symbol(symbol: str, path: Path) -> list[dict]:
    settings = get_settings()
    df = pd.read_csv(path)
    df = add_all_indicators(df, settings).dropna().reset_index(drop=True)

    groups = {
        "trend_ma_ema": lambda row, prev: signal_trend(row),
        "rsi": lambda row, prev: signal_rsi(row),
        "macd_histogram": lambda row, prev: signal_macd(row, prev),
        "stochastic": lambda row, prev: signal_stochastic(row),
        "bollinger_middle": lambda row, prev: signal_bollinger(row),
        "candle_body": lambda row, prev: signal_candle(row),
    }

    stats = {name: {"wins": 0, "losses": 0, "signals": 0} for name in groups}

    for index in range(1, len(df) - 1):
        row = df.iloc[index]
        previous = df.iloc[index - 1]
        next_row = df.iloc[index + 1]

        for name, signal_fn in groups.items():
            signal = signal_fn(row, previous)
            result = next_candle_result(signal, float(row["close"]), float(next_row["close"]))

            if result is None:
                continue

            stats[name]["signals"] += 1
            if result:
                stats[name]["wins"] += 1
            else:
                stats[name]["losses"] += 1

    rows = []
    for name, item in stats.items():
        signals = item["signals"]
        wins = item["wins"]
        losses = item["losses"]
        accuracy = wins / signals if signals else 0
        rows.append(
            {
                "symbol": symbol,
                "indicator_group": name,
                "signals": signals,
                "wins": wins,
                "losses": losses,
                "accuracy": round(accuracy, 4),
            }
        )

    return rows


def main() -> None:
    rows = []

    for symbol, path in DATA_FILES.items():
        if not path.exists():
            print(f"Arquivo nao encontrado: {path}. Rode python -m src.tools.generate_sample_data")
            continue

        rows.extend(evaluate_symbol(symbol, path))

    if not rows:
        print("Nenhum resultado gerado.")
        return

    rows.sort(key=lambda row: (row["accuracy"], row["signals"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Comparativo de grupos de indicadores:")
    for row in rows[:20]:
        print(
            f"{row['symbol']} | {row['indicator_group']} | "
            f"acerto {row['accuracy']:.2%} | sinais {row['signals']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: este teste usa dados disponiveis localmente e nao garante resultado real.")


if __name__ == "__main__":
    main()
