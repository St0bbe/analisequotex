# Integração com candles reais

Sim. Para o sistema melhorar com base em porcentagem real, ele precisa sair dos candles simulados e passar a receber candles reais do mercado.

## Por que isso é necessário?

Os resultados atuais servem para validar:

- lógica dos indicadores;
- janela de entrada;
- filtros de confiança;
- relatórios;
- fluxo do runner.

Mas eles ainda não representam o comportamento real da plataforma.

Para estimar melhor a chance de acerto, precisamos de:

1. candles reais;
2. histórico dos sinais gerados;
3. resultado de cada sinal após a vela fechar;
4. atualização dos relatórios de win rate.

## Fluxo ideal

```txt
Candles reais
   ↓
Indicadores técnicos
   ↓
Sinal BUY / SELL / WAIT
   ↓
Registro do sinal
   ↓
Aguardar a vela finalizar
   ↓
Comparar direção do sinal com o fechamento real
   ↓
Marcar WIN / LOSS / DRAW
   ↓
Atualizar estatísticas por ativo
```

## O que foi preparado no código

Foi criada uma interface para fontes de candles:

```txt
src/data/base.py
```

Agora o scanner pode receber diferentes fontes de candles:

```txt
SimulatedCandleFeed  -> candles simulados
CsvCandleFeed        -> candles vindos de arquivo CSV
FutureRealCandleFeed -> candles reais de uma API, WebSocket ou exportação externa
```

## Formato esperado de CSV

Cada arquivo de candles deve ter colunas:

```csv
timestamp,open,high,low,close
2026-07-05T14:30:00,1.26800,1.26850,1.26780,1.26820
```

Exemplo de nome para M1:

```txt
data/gbpusd_otc_m1.csv
```

## Próximo passo técnico

Criar um adapter real para a fonte escolhida.

Opções possíveis:

- CSV exportado da plataforma;
- API de cotações;
- WebSocket de mercado;
- scraping controlado apenas se for permitido pela plataforma;
- integração com corretora/plataforma que ofereça dados de candles.

## Importante

A automação de entrada real não deve ser feita antes de validar bem os sinais com candles reais e registrar os resultados reais das velas.
