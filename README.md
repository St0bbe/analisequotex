# Analise Quotex

Projeto inicial para um robo de analise e sinais de mercado inspirado no fluxo da Quotex.

> Importante: este projeto foi estruturado primeiro como **robo de sinais e simulacao**, sem executar entradas automaticas em conta real. Plataformas como Quotex normalmente nao oferecem API oficial publica para automacao, entao a versao inicial foca em analise, alertas, historico e testes com seguranca.

## Objetivo

Criar uma base profissional para:

- Ler candles de uma fonte configuravel.
- Calcular indicadores tecnicos.
- Gerar sinais de COMPRA, VENDA ou AGUARDAR.
- Registrar os sinais em arquivo.
- Rodar em modo simulado para validar estrategia.
- Evoluir depois para dashboard web, Telegram, banco de dados e backtesting.

## Stack inicial

- Python 3.11+
- Pandas
- NumPy
- python-dotenv
- Rich para exibicao no terminal

## Estrutura

```txt
analisequotex/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── data/
│   │   └── simulated_feed.py
│   ├── indicators/
│   │   └── technical.py
│   ├── strategy/
│   │   └── rsi_ma_strategy.py
│   └── storage/
│       └── signal_logger.py
├── .env.example
├── requirements.txt
└── README.md
```

## Como rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python src/main.py
```

No Linux/Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## Como funciona agora

A versao inicial usa um feed simulado de candles para testar a logica sem depender de login, token ou corretora.

A estrategia atual combina:

- Media movel curta.
- Media movel longa.
- RSI.

Ela gera:

- `BUY` quando ha tendencia de alta e RSI favoravel.
- `SELL` quando ha tendencia de baixa e RSI favoravel.
- `WAIT` quando nao ha confirmacao suficiente.

## Proximas etapas recomendadas

1. Validar a estrategia em modo simulado.
2. Adicionar backtesting com CSV historico.
3. Criar painel web com React ou Streamlit.
4. Adicionar alerta via Telegram.
5. Estudar a viabilidade tecnica e juridica de qualquer integracao com corretora.

## Aviso de risco

Este projeto nao garante lucro e nao deve ser usado como recomendacao financeira. Operacoes de curto prazo e opcoes binarias possuem alto risco. Teste sempre em ambiente demo antes de qualquer decisao real.
