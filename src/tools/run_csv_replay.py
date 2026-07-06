from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from src.config import get_settings
from src.models import Candle
from src.strategy.confluence_strategy import ConfluenceStrategy
from src.win_rate import estimated_win_rate_for, load_combined_win_rates, passes_min_win_rate


DATA_DIR = Path("data")
RESULTS_PATH = Path("csv_replay_results.csv")
PERFORMANCE_PATH = Path("csv_replay_performance_report.csv")
EMPIRICAL_PATH = Path("empirical_win_rates.csv")
OPPORTUNITY_PATH = Path("csv_replay_opportunity_report.csv")


DEFAULT_SYMBOLS = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay historico de candles CSV M1")
    parser.add_argument("--symbols", nargs="+", default=None, help="Ativos para testar. Exemplo: --symbols GBPUSD-OTC")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Pasta dos CSVs")
    parser.add_argument("--min-win-rate", type=float, default=53.0, help="Filtro minimo de win rate combinado")
    parser.add_argument("--include-all-signals", action="store_true", help="Inclui todos os sinais BUY/SELL, mesmo abaixo do filtro")
    parser.add_argument("--max-rows", type=int, default=None, help="Limite opcional de candles por ativo")
    parser.add_argument("--fresh", action="store_true", help="Limpa relatorios anteriores do replay")
    parser.add_argument(
        "--direction-mode",
        choices=["normal", "inverted", "auto"],
        default="normal",
        help="Modo de direcao: normal, inverted ou auto com base no relatorio de oportunidades.",
    )
    return parser.parse_args()


def symbol_to_csv_path(symbol: str, data_dir: Path) -> Path:
    filename = f"{symbol.lower().replace('-', '_')}_m1.csv"
    return data_dir / filename


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def load_candles(path: Path, max_rows: int | None = None) -> list[Candle]:
    candles: list[Candle] = []

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"timestamp", "open", "high", "low", "close"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV {path} sem colunas obrigatorias: {', '.join(sorted(missing))}")

        for index, row in enumerate(reader):
            if max_rows is not None and index >= max_rows:
                break

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


def should_invert(symbol: str, side: str, filter_status: str, direction_mode: str, opportunity_map: set[tuple[str, str, str]]) -> bool:
    if direction_mode == "inverted":
        return True

    if direction_mode == "auto":
        return (symbol, side, filter_status) in opportunity_map

    return False


def load_auto_inversion_map(path: Path = OPPORTUNITY_PATH) -> set[tuple[str, str, str]]:
    if not path.exists():
        return set()

    items: set[tuple[str, str, str]] = set()
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("recommendation") != "INVERSAO_PROMISSORA":
                continue
            items.add((row["symbol"], row["side"], row.get("filter_status", "UNKNOWN")))

    return items


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


def reset_outputs() -> None:
    for path in [RESULTS_PATH, PERFORMANCE_PATH]:
        if path.exists():
            path.unlink()


def write_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        return

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_performance_rows(results: list[dict]) -> list[dict]:
    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    for row in results:
        result = row["result"]
        if result not in {"WIN", "LOSS", "DRAW"}:
            continue

        key = (row["symbol"], row["effective_side"], row["filter_status"], row["direction_mode"])
        stats[key]["total"] += 1
        stats[key][result.lower()] += 1

    rows = []
    for (symbol, effective_side, filter_status, direction_mode), item in stats.items():
        total = item["total"]
        win = item["win"]
        loss = item["loss"]
        draw = item["draw"]
        win_rate = win / total if total else 0
        rows.append(
            {
                "symbol": symbol,
                "effective_side": effective_side,
                "filter_status": filter_status,
                "direction_mode": direction_mode,
                "total": total,
                "win": win,
                "loss": loss,
                "draw": draw,
                "win_rate_percent": round(win_rate * 100, 2),
            }
        )

    rows.sort(key=lambda row: (row["win_rate_percent"], row["total"]), reverse=True)
    return rows


def build_empirical_rows(results: list[dict], min_samples: int = 10) -> list[dict]:
    stats = defaultdict(lambda: {"total": 0, "win": 0, "loss": 0, "draw": 0})

    for row in results:
        result = row["result"]
        if result not in {"WIN", "LOSS", "DRAW"}:
            continue

        symbol = row["symbol"]
        stats[symbol]["total"] += 1
        stats[symbol][result.lower()] += 1

    rows = []
    for symbol, item in stats.items():
        total = item["total"]
        win = item["win"]
        loss = item["loss"]
        draw = item["draw"]
        win_rate = win / total if total else 0
        rows.append(
            {
                "symbol": symbol,
                "empirical_win_rate_percent": round(win_rate * 100, 2),
                "total": total,
                "win": win,
                "loss": loss,
                "draw": draw,
                "sample_status": "CONFIAVEL" if total >= min_samples else "POUCOS_DADOS",
                "source_file": str(RESULTS_PATH),
            }
        )

    rows.sort(key=lambda row: (row["sample_status"] == "CONFIAVEL", row["empirical_win_rate_percent"], row["total"]), reverse=True)
    return rows


def replay_symbol(
    symbol: str,
    candles: list[Candle],
    include_all: bool,
    min_win_rate: float,
    win_rates: dict[str, float],
    direction_mode: str,
    opportunity_map: set[tuple[str, str, str]],
) -> list[dict]:
    settings = get_settings()
    strategy = ConfluenceStrategy(settings)
    rows: list[dict] = []

    if len(candles) <= settings.candle_limit + 1:
        print(f"{symbol}: poucos candles para replay. Necessario mais que {settings.candle_limit + 1}.")
        return rows

    for index in range(settings.candle_limit, len(candles) - 1):
        window = candles[index - settings.candle_limit:index]
        next_candle = candles[index]
        signal = strategy.analyze(symbol, window)

        if signal.side.value == "WAIT":
            continue

        combined = estimated_win_rate_for(symbol, win_rates)
        passed_filter = passes_min_win_rate(symbol, win_rates, min_win_rate)
        filter_status = "PASSED" if passed_filter else "BELOW_FILTER"

        if not include_all and not passed_filter:
            continue

        original_side = signal.side.value
        inverted = should_invert(symbol, original_side, filter_status, direction_mode, opportunity_map)
        effective_side = opposite_side(original_side) if inverted else original_side
        applied_direction = "inverted" if inverted else "normal"

        rows.append(
            {
                "signal_time": window[-1].timestamp.isoformat(),
                "evaluated_candle_time": next_candle.timestamp.isoformat(),
                "feed": "csv_replay",
                "symbol": symbol,
                "original_side": original_side,
                "effective_side": effective_side,
                "confidence": round(signal.confidence, 4),
                "combined_win_rate": combined if combined is not None else "",
                "entry_price": signal.price,
                "exit_price": next_candle.close,
                "result": evaluate(effective_side, signal.price, next_candle.close),
                "filter_status": filter_status,
                "direction_mode": applied_direction,
                "reason": signal.reason,
            }
        )

    return rows


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    symbols = tuple(args.symbols) if args.symbols else DEFAULT_SYMBOLS

    if args.fresh:
        reset_outputs()

    win_rates = load_combined_win_rates()
    opportunity_map = load_auto_inversion_map() if args.direction_mode == "auto" else set()
    all_results: list[dict] = []

    print("CSV Replay iniciado.")
    print(f"Pasta de dados: {data_dir}")
    print(f"Ativos: {', '.join(symbols)}")
    print(f"Filtro minimo: {args.min_win_rate:.2f}%")
    print(f"Modo de direcao: {args.direction_mode}")
    if args.direction_mode == "auto":
        print(f"Regras de inversao carregadas: {len(opportunity_map)}")
    if args.include_all_signals:
        print("Modo coleta: incluindo todos os sinais BUY/SELL.")

    for symbol in symbols:
        path = symbol_to_csv_path(symbol, data_dir)
        if not path.exists():
            print(f"{symbol}: arquivo nao encontrado: {path}")
            continue

        candles = load_candles(path, args.max_rows)
        rows = replay_symbol(
            symbol=symbol,
            candles=candles,
            include_all=args.include_all_signals,
            min_win_rate=args.min_win_rate,
            win_rates=win_rates,
            direction_mode=args.direction_mode,
            opportunity_map=opportunity_map,
        )
        all_results.extend(rows)
        print(f"{symbol}: {len(rows)} sinais avaliados em replay.")

    if not all_results:
        print("Nenhum sinal avaliado. Verifique os CSVs ou use --include-all-signals.")
        return

    write_rows(RESULTS_PATH, all_results)
    performance_rows = build_performance_rows(all_results)
    empirical_rows = build_empirical_rows(all_results)
    write_rows(PERFORMANCE_PATH, performance_rows)
    write_rows(EMPIRICAL_PATH, empirical_rows)

    print("\nPerformance do replay:")
    for row in performance_rows[:20]:
        print(
            f"{row['symbol']} {row['effective_side']} {row['filter_status']} {row['direction_mode']} | "
            f"win rate {row['win_rate_percent']}% | total {row['total']} | "
            f"WIN {row['win']} | LOSS {row['loss']} | DRAW {row['draw']}"
        )

    print(f"\nResultados salvos em {RESULTS_PATH}")
    print(f"Performance salva em {PERFORMANCE_PATH}")
    print(f"Win rates empiricos atualizados em {EMPIRICAL_PATH}")
    print("Aviso: a qualidade depende totalmente da origem dos candles CSV.")


if __name__ == "__main__":
    main()
