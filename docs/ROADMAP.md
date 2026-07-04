# Roadmap do robo de analise

Este projeto sera evoluido em fases para evitar uma base fraca e dificil de manter.

## Fase 1 - Motor de analise local

Objetivo: criar o nucleo do robo sem depender de corretora.

- Timeframe principal: M1.
- Ativos iniciais: EURUSD, GBPUSD, USDJPY e versoes OTC.
- Feed inicial: simulado.
- Saida: alertas educacionais e classificacao de tendencia.
- Historico: arquivo CSV.

## Fase 2 - Estrategia forte com confluencias

A estrategia inicial sera baseada em pontuacao, usando varios filtros:

- Direcao da tendencia por medias moveis.
- Forca por RSI.
- Regiao por Bollinger Bands.
- Momentum por MACD.
- Volatilidade minima.
- Evitar alertas quando o mercado estiver lateral.

A ideia nao e confiar em um unico indicador, mas exigir confluencia.

## Fase 3 - Backtesting

- Rodar estrategia em CSV historico.
- Calcular taxa de acerto.
- Calcular sequencia de perdas.
- Separar resultado por ativo.
- Separar resultado por horario.
- Encontrar os ativos e horarios mais fortes.

## Fase 4 - Dashboard

- Painel web em tempo real.
- Ranking dos melhores ativos no momento.
- Historico de alertas.
- Indicadores na tela.
- Estatisticas por estrategia.

## Fase 5 - Alertas

- Telegram.
- Som no painel.
- Notificacao visual.

## Fase 6 - Integracoes externas

Qualquer integracao com corretora deve ser analisada com cuidado, principalmente quando nao houver API oficial publica. A prioridade do projeto sera seguranca, estabilidade e validacao da estrategia antes de qualquer execucao automatizada.

## Regras de seguranca do projeto

- Nunca salvar senha no codigo.
- Nunca commitar tokens.
- Testar primeiro em simulacao.
- Testar depois em demo.
- Medir resultado antes de qualquer uso real.
- Nao prometer lucro.
