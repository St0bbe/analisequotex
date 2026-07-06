from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import get_settings
from src.models import Candle
from src.strategy.confluence_strategy import ConfluenceStrategy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = PROJECT_ROOT / "public"

app = FastAPI(title="ROBO DE ANALISE MINIMALISTA")

if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_candles(csv_text: str) -> list[Candle]:
    candles: list[Candle] = []
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"CSV sem colunas obrigatorias: {', '.join(sorted(missing))}")

    for row in reader:
        candles.append(
            Candle(
                timestamp=parse_timestamp(row["timestamp"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
        )

    candles.sort(key=lambda candle: candle.timestamp)
    return candles


def opposite_side(side: str) -> str:
    if side == "BUY":
        return "SELL"
    if side == "SELL":
        return "BUY"
    return side


def evaluate(side: str, entry_price: float, exit_price: float) -> str:
    if side == "BUY":
        if exit_price > entry_price:
            return "WIN"
        if exit_price < entry_price:
            return "LOSS"
        return "DRAW"

    if side == "SELL":
        if exit_price < entry_price:
            return "WIN"
        if exit_price > entry_price:
            return "LOSS"
        return "DRAW"

    return "IGNORED"


def summarize(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], dict[str, int]] = {}

    for row in rows:
        key = (row["symbol"], row["effective_side"])
        if key not in grouped:
            grouped[key] = {"total": 0, "win": 0, "loss": 0, "draw": 0}

        result = row["result"]
        grouped[key]["total"] += 1
        if result == "WIN":
            grouped[key]["win"] += 1
        elif result == "LOSS":
            grouped[key]["loss"] += 1
        elif result == "DRAW":
            grouped[key]["draw"] += 1

    output = []
    for (symbol, side), item in grouped.items():
        total = item["total"]
        win_rate = item["win"] / total if total else 0
        output.append(
            {
                "symbol": symbol,
                "side": side,
                "total": total,
                "win": item["win"],
                "loss": item["loss"],
                "draw": item["draw"],
                "win_rate_percent": round(win_rate * 100, 2),
            }
        )

    output.sort(key=lambda row: (row["win_rate_percent"], row["total"]), reverse=True)
    return output


def run_replay(symbol: str, csv_text: str, direction_mode: Literal["normal", "inverted"] = "normal") -> dict:
    settings = get_settings()
    candles = parse_candles(csv_text)

    if len(candles) <= settings.candle_limit + 1:
        raise ValueError(f"Poucos candles. Envie mais que {settings.candle_limit + 1} linhas de candles.")

    strategy = ConfluenceStrategy(settings)
    rows = []

    for index in range(settings.candle_limit, len(candles) - 1):
        window = candles[index - settings.candle_limit:index]
        next_candle = candles[index]
        signal = strategy.analyze(symbol, window)

        if signal.side.value == "WAIT":
            continue

        original_side = signal.side.value
        effective_side = opposite_side(original_side) if direction_mode == "inverted" else original_side

        rows.append(
            {
                "signal_time": window[-1].timestamp.isoformat(),
                "evaluated_candle_time": next_candle.timestamp.isoformat(),
                "symbol": symbol,
                "original_side": original_side,
                "effective_side": effective_side,
                "confidence": round(signal.confidence, 4),
                "entry_price": signal.price,
                "exit_price": next_candle.close,
                "result": evaluate(effective_side, signal.price, next_candle.close),
                "direction_mode": direction_mode,
                "reason": signal.reason,
            }
        )

    return {
        "symbol": symbol,
        "direction_mode": direction_mode,
        "total_signals": len(rows),
        "summary": summarize(rows),
        "rows": rows[:500],
        "limited_rows": len(rows) > 500,
    }


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    index_path = PUBLIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>ROBO DE ANALISE MINIMALISTA</h1><p>Interface nao encontrada.</p>")


@app.post("/api/replay")
def replay(
    symbol: str = Form(...),
    direction_mode: Literal["normal", "inverted"] = Form("normal"),
    csv_text: str = Form(...),
) -> JSONResponse:
    try:
        result = run_replay(symbol=symbol.strip().upper(), csv_text=csv_text, direction_mode=direction_mode)
        return JSONResponse(result)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": "ROBO DE ANALISE MINIMALISTA"}
