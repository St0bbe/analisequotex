# Arquitetura alvo

## Visao geral

```txt
Fonte de candles
      |
      v
Market Data Adapter
      |
      v
Indicator Engine
      |
      v
Strategy Engine
      |
      +--> Signal Score
      +--> Risk Filter
      +--> Alert Manager
      |
      v
Storage + Dashboard
```

## Modulos

### 1. Market Data Adapter

Responsavel por padronizar candles vindos de diferentes fontes.

No inicio teremos:

- Feed simulado.
- Leitura futura de CSV.
- Possivel conector externo se houver fonte estavel.

### 2. Indicator Engine

Calcula indicadores reutilizaveis:

- RSI.
- Medias moveis.
- EMA de tendencia.
- Bollinger Bands.
- MACD.
- Volatilidade.

### 3. Strategy Engine

Combina os indicadores e gera uma pontuacao final por ativo.

A estrategia nao deve decidir com base em apenas um indicador. O objetivo e exigir confluencias.

### 4. Risk Filter

Filtros para evitar momentos ruins:

- Mercado lateral.
- Baixa volatilidade.
- Excesso de sinais no mesmo ativo.
- Horarios ruins identificados no backtesting.

### 5. Alert Manager

Saidas planejadas:

- Terminal.
- CSV.
- Telegram.
- Dashboard web.

### 6. Dashboard

Stack sugerida:

- Backend: FastAPI.
- Frontend: React + Vite + Tailwind.
- Banco: PostgreSQL ou SQLite no inicio.

## Decisao tecnica inicial

A primeira etapa sera Python puro para validar a inteligencia. Depois criaremos API e dashboard.
