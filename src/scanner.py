from __future__ import annotations

from dataclasses import dataclass

from src.config import Settings
from src.data.simulated_feed import SimulatedCandleFeed
from src.models import MarketSignal, SignalSide
from src.strategy.confluence_strategy import ConfluenceStrategy


@dataclass(frozen=True)
class ScanResult:
    signals: list[MarketSignal]

    @property
    def actionable(self) -> list[MarketSignal]:
        return [signal for signal in self.signals if signal.side != SignalSide.WAIT]

    @property
    def ranked(self) -> list[MarketSignal]:
        return sorted(self.signals, key=lambda item: item.confidence, reverse=True)


class MultiAssetScanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.strategy = ConfluenceStrategy(settings)

    def scan_once(self) -> ScanResult:
        return self.scan_symbols(self.settings.symbols)

    def scan_priority(self) -> ScanResult:
        return self.scan_symbols(self.settings.priority_symbols)

    def scan_symbols(self, symbols: tuple[str, ...]) -> ScanResult:
        signals: list[MarketSignal] = []

        for symbol in symbols:
            seed_price = self._initial_price_for(symbol)
            feed = SimulatedCandleFeed(initial_price=seed_price)
            candles = feed.get_recent_candles(self.settings.candle_limit)
            signal = self.strategy.analyze(symbol, candles)
            signals.append(signal)

        return ScanResult(signals=signals)

    def _initial_price_for(self, symbol: str) -> float:
        normalized = symbol.replace("-OTC", "")

        if normalized == "USDJPY":
            return 157.50

        if normalized == "GBPUSD":
            return 1.2700

        return 1.1000
