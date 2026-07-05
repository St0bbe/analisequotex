# Compatibilidade com plataformas

Este projeto foi desenhado para separar o motor de analise da plataforma usada para operar.

## Como pensar a arquitetura

```txt
Fonte de candles / plataforma
        |
        v
Adapter de dados
        |
        v
Motor de indicadores
        |
        v
Estrategia por confluencia
        |
        v
Scanner / alertas / dashboard
```

## O que isso significa

O mesmo motor de analise pode ser reaproveitado para diferentes fontes, desde que exista um adapter capaz de entregar candles no formato padrao do projeto:

```txt
timestamp, open, high, low, close
```

## Status por plataforma

| Plataforma | Analise e sinais | Entrada automatica |
| --- | --- | --- |
| Quotex | Possivel com adapter de dados | Apenas se houver meio permitido e estavel |
| Pocket Option | Possivel com adapter de dados | Apenas se houver meio permitido e estavel |
| Outras corretoras | Possivel com adapter de dados | Recomendado somente com API oficial |

## Importante

A prioridade do projeto e construir uma plataforma de analise, simulacao, backtesting e alertas.

A execucao automatica de ordens reais nao deve ser implementada sem validar:

- Se existe API oficial.
- Se a automacao e permitida pelos termos da plataforma.
- Se o fluxo e estavel.
- Se foi testado primeiro em simulacao e demo.
- Se nao ha risco de expor login, senha ou token no codigo.

## Proximo passo tecnico

Criar interfaces de adapter:

- `SimulatedMarketDataAdapter`
- `CsvMarketDataAdapter`
- `PocketOptionMarketDataAdapter` futuramente, caso exista fonte confiavel de candles
- `QuotexMarketDataAdapter` futuramente, caso exista fonte confiavel de candles
