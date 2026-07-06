# Analise Quotex

Projeto de analise estatistica e validacao de sinais M1 inspirado no fluxo de plataformas como Quotex/Pocket Option.

> Importante: este projeto e focado em **analise, replay, validacao em papel e sinais simulados**. Ele nao envia ordens reais e nao garante lucro. Use como ferramenta de estudo estatistico.

## Status do MVP

O MVP atual esta focado em uma solucao gratuita baseada em CSV Replay:

- Calcula indicadores tecnicos.
- Gera sinais BUY, SELL ou WAIT.
- Testa candles historicos em CSV rapidamente.
- Avalia WIN, LOSS e DRAW pela proxima vela.
- Gera relatorios de performance.
- Calcula win rate empirico.
- Detecta quando a direcao invertida performa melhor.
- Permite modo de direcao normal, inverted ou auto.
- Possui validacao em papel para confirmar vela por vela.

## Requisitos

- Python 3.11+
- Windows PowerShell, CMD, Linux ou Mac
- Dependencias do `requirements.txt`

Instalacao no Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Estrutura principal

```txt
src/
├── config.py
├── models.py
├── scanner.py
├── live_signal_runner.py
├── paper_validation_runner.py
├── data/
│   ├── simulated_feed.py
│   ├── csv_feed.py
│   └── oanda_feed.py
├── indicators/
│   └── technical.py
├── strategy/
│   └── confluence_strategy.py
├── storage/
│   ├── signal_logger.py
│   └── result_logger.py
└── tools/
    ├── generate_sample_data.py
    ├── run_csv_replay.py
    ├── analyze_csv_replay_opportunities.py
    ├── build_real_performance_report.py
    ├── build_empirical_win_rates.py
    └── analyze_filter_performance.py
```

## Fluxo recomendado gratuito

### 1. Gerar CSVs simulados para teste

```powershell
python -m src.tools.generate_sample_data
```

Isso cria arquivos em `data/`, por exemplo:

```txt
data/eurusd_m1.csv
data/gbpusd_m1.csv
data/usdjpy_m1.csv
data/eurusd_otc_m1.csv
data/gbpusd_otc_m1.csv
data/usdjpy_otc_m1.csv
```

### 2. Rodar replay normal

```powershell
python -m src.tools.run_csv_replay --include-all-signals --fresh
```

Relatorios gerados:

```txt
csv_replay_results.csv
csv_replay_performance_report.csv
empirical_win_rates.csv
```

### 3. Analisar se existe inversao promissora

```powershell
python -m src.tools.analyze_csv_replay_opportunities
notepad csv_replay_opportunity_report.csv
```

Esse relatorio compara o resultado normal contra o resultado invertido.

### 4. Rodar replay com direcao automatica

```powershell
python -m src.tools.run_csv_replay --include-all-signals --direction-mode auto --fresh
notepad csv_replay_performance_report.csv
```

O modo `auto` usa `csv_replay_opportunity_report.csv` para inverter apenas grupos marcados como `INVERSAO_PROMISSORA`.

## Validacao em papel

A validacao em papel espera a proxima vela fechar. Por isso ela demora. Use apenas para confirmar em tempo real/simulado depois do replay.

Comando rapido:

```powershell
.\scripts\run_paper_validation.ps1 -Feed simulated -Cycles 5 -DirectionMode auto -IncludeAllSignals
```

Comando mais longo:

```powershell
.\scripts\run_paper_validation.ps1 -Feed simulated -Cycles 30 -DirectionMode auto
```

Relatorios:

```txt
paper_validation_results.csv
real_performance_report.csv
empirical_win_rates.csv
```

## Modos de direcao

O replay e a validacao aceitam:

```txt
normal   -> usa o sinal original
inverted -> inverte BUY para SELL e SELL para BUY
auto     -> inverte apenas grupos promissores do relatorio de oportunidade
```

Exemplo:

```powershell
python -m src.tools.run_csv_replay --include-all-signals --direction-mode auto --fresh
```

## Formato de CSV aceito

Cada CSV precisa ter as colunas:

```csv
timestamp,open,high,low,close
```

Exemplo:

```csv
2026-07-06T20:00:00,1.2680,1.2690,1.2675,1.2685
```

Nome esperado por ativo:

```txt
EURUSD      -> data/eurusd_m1.csv
GBPUSD      -> data/gbpusd_m1.csv
USDJPY      -> data/usdjpy_m1.csv
EURUSD-OTC  -> data/eurusd_otc_m1.csv
GBPUSD-OTC  -> data/gbpusd_otc_m1.csv
USDJPY-OTC  -> data/usdjpy_otc_m1.csv
```

## Fonte de candles

O projeto nao depende de API paga. O caminho principal do MVP e importar candles via CSV.

Fontes possiveis:

- CSV proprio/exportado.
- Dados gratuitos de terceiros, se permitirem uso.
- API oficial, se existir e se for gratuita.
- OANDA apenas como opcional para Forex real, se voce tiver token disponivel.

Evite depender de scraping do TradingView ou WebSocket interno de plataformas sem permissao.

## Comandos principais

Replay completo:

```powershell
python -m src.tools.run_csv_replay --include-all-signals --direction-mode auto --fresh
```

Relatorio de oportunidade:

```powershell
python -m src.tools.analyze_csv_replay_opportunities
```

Validacao em papel:

```powershell
.\scripts\run_paper_validation.ps1 -Feed simulated -Cycles 5 -DirectionMode auto -IncludeAllSignals
```

Relatorio de performance:

```powershell
python -m src.tools.build_real_performance_report
```

Win rate empirico:

```powershell
python -m src.tools.build_empirical_win_rates
```

## Quando considerar um resultado confiavel

Use pelo menos:

```txt
30 a 50 sinais por ativo/direcao para observacao inicial
100+ sinais para uma leitura mais seria
```

Resultados com poucas amostras devem ser tratados como `POUCOS_DADOS`.

## Aviso de risco

Este projeto nao e recomendacao financeira. Operacoes de curto prazo e opcoes binarias possuem alto risco. Os resultados de replay, simulacao ou validacao em papel nao garantem resultado futuro. Use sempre com dados suficientes, ambiente demo e gestao de risco.
