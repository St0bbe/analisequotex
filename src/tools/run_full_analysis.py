from __future__ import annotations

from src.tools import (
    analyze_signals,
    build_dashboard,
    estimate_win_rate,
    generate_sample_data,
    optimize_confidence,
    rank_assets,
    run_backtest_report,
)


def main() -> None:
    print("1/7 - Gerando dados historicos simulados...")
    generate_sample_data.main()

    print("\n2/7 - Rodando backtest...")
    run_backtest_report.main()

    print("\n3/7 - Otimizando confianca por ativo...")
    optimize_confidence.main()

    print("\n4/7 - Analisando sinais do runner...")
    analyze_signals.main()

    print("\n5/7 - Gerando ranking operacional...")
    rank_assets.main()

    print("\n6/7 - Estimando chance de win por ativo...")
    estimate_win_rate.main()

    print("\n7/7 - Construindo dashboard local...")
    build_dashboard.main()

    print("\nPipeline completo finalizado.")
    print("Abra o painel com: start dashboard.html")


if __name__ == "__main__":
    main()
