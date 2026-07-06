from __future__ import annotations

import csv
from pathlib import Path
from html import escape


DASHBOARD_PATH = Path("dashboard.html")
REPORTS = {
    "Ranking de Ativos": Path("asset_ranking_report.csv"),
    "Resumo dos Sinais": Path("signals_summary.csv"),
    "Melhores Confianças": Path("best_confidence_report.csv"),
    "Backtest": Path("backtest_report.csv"),
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_table(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section><h2>{escape(title)}</h2><p class='empty'>Relatório ainda não gerado.</p></section>"

    headers = list(rows[0].keys())
    head_html = "".join(f"<th>{escape(header)}</th>" for header in headers)

    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(header, '')))}</td>" for header in headers)
        body_rows.append(f"<tr>{cells}</tr>")

    body_html = "".join(body_rows)
    return f"""
    <section>
      <h2>{escape(title)}</h2>
      <div class="table-wrap">
        <table>
          <thead><tr>{head_html}</tr></thead>
          <tbody>{body_html}</tbody>
        </table>
      </div>
    </section>
    """


def main() -> None:
    sections = []

    for title, path in REPORTS.items():
        sections.append(build_table(title, read_csv(path)))

    html = f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard Analise Quotex</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --card: #111833;
      --muted: #9aa4c7;
      --text: #f5f7ff;
      --line: #253055;
      --accent: #7dd3fc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: radial-gradient(circle at top, #182348 0%, var(--bg) 45%);
      color: var(--text);
      padding: 32px;
    }}
    header {{
      max-width: 1200px;
      margin: 0 auto 28px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    p {{ color: var(--muted); }}
    section {{
      max-width: 1200px;
      margin: 0 auto 24px;
      padding: 22px;
      background: rgba(17, 24, 51, 0.9);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 20px 60px rgba(0,0,0,.25);
    }}
    h2 {{ margin-top: 0; color: var(--accent); }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      font-size: 14px;
    }}
    th {{ color: var(--accent); font-weight: 700; }}
    tr:hover td {{ background: rgba(125, 211, 252, 0.06); }}
    .empty {{ color: var(--muted); }}
    .notice {{
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(125, 211, 252, 0.08);
    }}
  </style>
</head>
<body>
  <header>
    <h1>Dashboard Analise Quotex</h1>
    <p class="notice">Painel local gerado a partir dos CSVs de simulação. Nenhuma ordem real é enviada.</p>
  </header>
  {''.join(sections)}
</body>
</html>
"""

    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard gerado em {DASHBOARD_PATH}")
    print("Abra com: start dashboard.html")


if __name__ == "__main__":
    main()
