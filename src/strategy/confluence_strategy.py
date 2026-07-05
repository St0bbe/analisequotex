from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.config import Settings
from src.indicators.technical import (
    add_all_indicators,
    candles_to_dataframe,
)
from src.models import Candle, MarketSignal, SignalSide


@dataclass(frozen=True)
class StrategyScore:
    side: SignalSide
    score: float
    reasons: list[str]


class ConfluenceStrategy:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, symbol: str, candles: list[Candle]) -> MarketSignal:
        if len(candles) < self.settings.candle_limit // 2:
            price = candles[-1].close if candles else 0.0
            return MarketSignal(symbol, SignalSide.WAIT, 0.0, "Dados insuficientes.", price, datetime.utcnow())

        df = candles_to_dataframe(candles)
        df = add_all_indicators(df, self.settings)
        df = df.dropna()

        if df.empty:
            price = candles[-1].close
            return MarketSignal(symbol, SignalSide.WAIT, 0.0, "Indicadores ainda sem dados validos.", price, datetime.utcnow())

        last = df.iloc[-1]
        previous = df.iloc[-2]
        price = float(last["close"])

        bullish_score = 0.0
        bearish_score = 0.0
        bullish_reasons: list[str] = []
        bearish_reasons: list[str] = []

        if float(last["fast_ma"]) > float(last["slow_ma"]) > 0:
            bullish_score += 0.20
            bullish_reasons.append("media rapida acima da media lenta")
        elif float(last["fast_ma"]) < float(last["slow_ma"]):
            bearish_score += 0.20
            bearish_reasons.append("media rapida abaixo da media lenta")

        if price > float(last["ema_trend"]):
            bullish_score += 0.16
            bullish_reasons.append("preco acima da EMA de tendencia")
        elif price < float(last["ema_trend"]):
            bearish_score += 0.16
            bearish_reasons.append("preco abaixo da EMA de tendencia")

        rsi = float(last["rsi"])
        if 48 <= rsi <= 66:
            bullish_score += 0.14
            bullish_reasons.append(f"RSI comprador equilibrado ({rsi:.2f})")
        elif 34 <= rsi <= 52:
            bearish_score += 0.14
            bearish_reasons.append(f"RSI vendedor equilibrado ({rsi:.2f})")

        if float(last["macd_histogram"]) > float(previous["macd_histogram"]):
            bullish_score += 0.14
            bullish_reasons.append("histograma MACD ganhando forca")
        elif float(last["macd_histogram"]) < float(previous["macd_histogram"]):
            bearish_score += 0.14
            bearish_reasons.append("histograma MACD perdendo forca")

        stoch_k = float(last["stoch_k"])
        stoch_d = float(last["stoch_d"])
        if stoch_k > stoch_d and 20 <= stoch_k <= 80:
            bullish_score += 0.08
            bullish_reasons.append(f"estocastico favorece alta ({stoch_k:.2f})")
        elif stoch_k < stoch_d and 20 <= stoch_k <= 80:
            bearish_score += 0.08
            bearish_reasons.append(f"estocastico favorece baixa ({stoch_k:.2f})")

        bb_middle = float(last["bb_middle"])
        if price > bb_middle:
            bullish_score += 0.08
            bullish_reasons.append("preco acima da media das Bollinger")
        elif price < bb_middle:
            bearish_score += 0.08
            bearish_reasons.append("preco abaixo da media das Bollinger")

        if bool(last["is_bullish_candle"]) and float(last["body_ratio"]) >= 0.35:
            bullish_score += 0.06
            bullish_reasons.append("candle atual comprador")
        elif bool(last["is_bearish_candle"]) and float(last["body_ratio"]) >= 0.35:
            bearish_score += 0.06
            bearish_reasons.append("candle atual vendedor")

        volatility = float(last["volatility"])
        volatility_ratio = volatility / price if price else 0.0
        bb_width = float(last["bb_width"])
        atr_ratio = float(last["atr_ratio"])
        has_enough_volatility = (
            volatility_ratio >= self.settings.min_volatility_ratio
            or atr_ratio >= self.settings.min_volatility_ratio
            or bb_width >= self.settings.min_bollinger_width
        )

        if has_enough_volatility:
            bullish_score += 0.08
            bearish_score += 0.08
        else:
            return MarketSignal(
                symbol,
                SignalSide.WAIT,
                0.35,
                f"Volatilidade proporcional baixa; melhor aguardar. ATR%={atr_ratio:.6f}, BB%={bb_width:.6f}.",
                price,
                datetime.utcnow(),
            )

        if bullish_score >= self.settings.min_confidence and bullish_score > bearish_score:
            return MarketSignal(
                symbol,
                SignalSide.BUY,
                round(bullish_score, 2),
                "Confluencia alta: " + "; ".join(bullish_reasons),
                price,
                datetime.utcnow(),
            )

        if bearish_score >= self.settings.min_confidence and bearish_score > bullish_score:
            return MarketSignal(
                symbol,
                SignalSide.SELL,
                round(bearish_score, 2),
                "Confluencia baixa: " + "; ".join(bearish_reasons),
                price,
                datetime.utcnow(),
            )

        return MarketSignal(
            symbol,
            SignalSide.WAIT,
            round(max(bullish_score, bearish_score), 2),
            f"Sem confluencia forte. Alta={bullish_score:.2f}, Baixa={bearish_score:.2f}.",
            price,
            datetime.utcnow(),
        )
