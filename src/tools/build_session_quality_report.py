from __future__ import annotations

import csv
from pathlib import Path


LIVE_SESSION_PATH = Path("live_session_summary.csv")
WIN_RATE_PATH = Path("win_rate_estimate.csv")
OUTPUT_PATH = Path("session_quality_report.csv")


def read_by_symbol(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return {row["symbol"]: row for row in csv.DictReader(file)}


def quality_label(rate: float | None, session_rate: float, confidence: float, total: int) -> str:
    if total < 5:
        return "POUCOS_DADOS"

    if rate is None:
        return "SEM_RELATORIO"

    if rate >= 55 and session_rate >= 0.40 and confidence >= 0.62:
        return "FORTE_EM_SIMULACAO"

    if rate >= 53 and session_rate >= 0.25 and confidence >= 0.60:
        return "OBSERVACAO"

    return "FRACO_NA_SESSAO"


def build_reason(rate: float | None, session_rate: float, confidence: float, total: int) -> str:
    reasons: list[str] = []

    if total < 5:
        reasons.append("poucos dados na sessao")

    if rate is None:
        reasons.append("sem taxa estimada de backtest")
    elif rate < 53:
        reasons.append("taxa estimada abaixo de 53%")
    elif rate < 55:
        reasons.append("taxa estimada aceitavel, mas abaixo de 55%")
    else:
        reasons.append("taxa estimada acima de 55%")

    if session_rate < 0.25:
        reasons.append("poucos sinais acionaveis na sessao")
    elif session_rate < 0.40:
        reasons.append("volume de sinais moderado")
    else:
        reasons.append("bom volume de sinais na sessao")

    if confidence < 0.60:
        reasons.append("confianca media baixa")
    elif confidence < 0.62:
        reasons.append("confianca media moderada")
    else:
        reasons.append("confianca media boa")

    return "; ".join(reasons)


def main() -> None:
    live_session = read_by_symbol(LIVE_SESSION_PATH)
    win_rates = read_by_symbol(WIN_RATE_PATH)

    if not live_session:
        print("live_session_summary.csv nao encontrado. Rode: python -m src.tools.analyze_live_session")
        return

    rows = []

    for symbol, session_row in live_session.items():
        total = int(session_row["total"])
        buy = int(session_row["buy"])
        sell = int(session_row["sell"])
        wait = int(session_row["wait"])
        session_rate = float(session_row["actionable_rate"])
        confidence = float(session_row["avg_confidence"])

        win_row = win_rates.get(symbol)
        rate = float(win_row["estimated_win_rate_percent"]) if win_row else None

        if buy > sell:
            dominant_side = "BUY"
        elif sell > buy:
            dominant_side = "SELL"
        else:
            dominant_side = "NEUTRO"

        rows.append(
            {
                "symbol": symbol,
                "quality": quality_label(rate, session_rate, confidence, total),
                "reason": build_reason(rate, session_rate, confidence, total),
                "dominant_side": dominant_side,
                "estimated_win_rate_percent": round(rate, 2) if rate is not None else "",
                "session_actionable_rate_percent": round(session_rate * 100, 2),
                "avg_confidence": round(confidence, 4),
                "total": total,
                "buy": buy,
                "sell": sell,
                "wait": wait,
            }
        )

    order = {
        "FORTE_EM_SIMULACAO": 3,
        "OBSERVACAO": 2,
        "POUCOS_DADOS": 1,
        "SEM_RELATORIO": 1,
        "FRACO_NA_SESSAO": 0,
    }
    rows.sort(key=lambda row: (order.get(row["quality"], 0), row["session_actionable_rate_percent"], row["avg_confidence"]), reverse=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Relatorio de qualidade da sessao:")
    for row in rows:
        print(
            f"{row['symbol']} | {row['quality']} | lado dominante {row['dominant_side']} | "
            f"taxa estimada {row['estimated_win_rate_percent']}% | "
            f"acionaveis na sessao {row['session_actionable_rate_percent']}% | "
            f"confianca media {row['avg_confidence']} | motivo: {row['reason']}"
        )

    print(f"Relatorio salvo em {OUTPUT_PATH}")
    print("Aviso: resultado simulado nao garante resultado real.")


if __name__ == "__main__":
    main()
