from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CandleWindow:
    timeframe_seconds: int = 60
    start_second: int = 48
    end_second: int = 55

    def elapsed_seconds(self, now: datetime | None = None) -> int:
        current = now or datetime.now()
        return current.second % self.timeframe_seconds

    def seconds_to_next_candle(self, now: datetime | None = None) -> int:
        elapsed = self.elapsed_seconds(now)
        return self.timeframe_seconds - elapsed

    def is_valid_analysis_time(self, now: datetime | None = None) -> bool:
        elapsed = self.elapsed_seconds(now)
        return self.start_second <= elapsed <= self.end_second

    def status_message(self, now: datetime | None = None) -> str:
        elapsed = self.elapsed_seconds(now)
        remaining = self.seconds_to_next_candle(now)

        if elapsed < self.start_second:
            return f"Aguardando janela final da vela. Faltam {self.start_second - elapsed}s para analisar."

        if elapsed <= self.end_second:
            return f"Janela ideal ativa. Faltam {remaining}s para a proxima vela."

        return f"Janela encerrada. Faltam {remaining}s para a proxima vela. Melhor aguardar."
