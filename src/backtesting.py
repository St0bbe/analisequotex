from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.models import Candle, SignalSide
from src.strategy.confluence_strategy import ConfluenceStrategy


@dataclass(frozen=True)
class BacktestSummary:
    symbol: str
    total_signals: int
    wins: int
    losses: int
    accuracy: float


class CsvBacktester:
    def __init__(self, csv_path: str, symbol: str) -> None:
        self.csv_path = Path(csv_path)
        self.symbol = symbol
        self.settings = get_settings()
        self.strategy = ConfluenceStrategy(self.settings)

    def run(self, lookahead_candles: int = 1) -> BacktestSummary:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        required_columns = {"timestamp", "open", "high", "low", "close"}
        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(f"CSV sem colunas obrigatorias: {', '.join(sorted(missing))}")

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        candles = [
            Candle(
                timestamp=row.timestamp.to_pydatetime(),
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
            )
            for row in df.itertuples(index=False)
        ]

        wins = 0
        losses = 0
        total_signals = 0
        window = self.settings.candle_limit

        for index in range(window, len(candles) - lookahead_candles):
            sample = candles[index - window : index]
            signal = self.strategy.analyze(self.symbol, sample)

            if signal.side == SignalSide.WAIT:
                continue

            total_signals += 1
            entry_price = candles[index].close
            exit_price = candles[index + lookahead_candles].close

            if signal.side == SignalSide.BUY and exit_price > entry_price:
                wins += 1
            elif signal.side == SignalSide.SELL and exit_price < entry_price:
                wins += 1
            else:
                losses += 1

        accuracy = wins / total_signals if total_signals else 0.0
        return BacktestSummary(self.symbol, total_signals, wins, losses, round(accuracy, 4))
