# Tempo ideal do sinal antes da entrada

Este projeto trabalha inicialmente com timeframe M1, ou seja, cada vela dura 60 segundos.

## Quando o sinal deve aparecer?

Para M1, o ideal e o sinal aparecer nos ultimos segundos da vela atual, antes da proxima vela iniciar.

Exemplo:

```txt
14:30:00 - vela atual inicia
14:30:50 - robo analisa a vela quase fechada
14:30:52 - painel mostra BUY, SELL ou WAIT
14:31:00 - proxima vela inicia
```

Nesse exemplo, o usuario teria aproximadamente 8 segundos para avaliar o sinal e tomar uma decisao manual.

## Janela recomendada

Para M1, a janela recomendada de analise e:

```txt
entre 8 e 12 segundos antes da proxima vela
```

Exemplo pratico:

```txt
Analisar entre xx:48 e xx:52
Exibir sinal entre xx:50 e xx:55
Entrada manual no inicio da proxima vela
```

## Por que nao analisar muito antes?

Se o robo gerar sinal com 30 ou 40 segundos de antecedencia, a vela atual ainda pode mudar muito.

Isso pode gerar falsos sinais.

## Por que nao analisar em cima da hora?

Se o robo gerar sinal faltando 1 ou 2 segundos, pode nao dar tempo para:

- o painel atualizar;
- o usuario ler o sinal;
- confirmar a entrada manual;
- lidar com atraso da internet ou da plataforma.

## Como sera implementado no projeto

O modo futuro em tempo real deve ter uma configuracao parecida com:

```txt
timeframe_seconds = 60
signal_window_start_seconds = 48
signal_window_end_seconds = 55
```

Ou seja:

- Antes de 48 segundos da vela: apenas monitorar.
- Entre 48 e 55 segundos: calcular e exibir sinal.
- Depois de 55 segundos: evitar novo sinal para nao ficar tarde demais.

## Sobre compra/venda automatica

A prioridade do projeto e gerar sinais e alertas.

Qualquer automacao de entrada real so deve ser estudada se houver integracao permitida, segura e estavel com a plataforma usada.

## Regra de seguranca

O sinal deve sempre mostrar:

- ativo;
- direcao: BUY, SELL ou WAIT;
- confianca;
- tempo restante para a proxima vela;
- motivo do sinal;
- aviso se o tempo restante estiver curto demais.
