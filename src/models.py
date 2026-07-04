from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


class SignalSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


@dataclass(frozen=True)
class MarketSignal:
    symbol: str
    side: SignalSide
    confidence: float
    reason: str
    price: float
    created_at: datetime
