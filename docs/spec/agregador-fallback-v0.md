# Agregador fallback v0

Status: implementado localmente
Versao: v0
Data: 2026-06-15
Produtor: `engine.agregador`
Consumidor: `engine.run`

## Objetivo

Criar uma fusao executavel antes do stacking/calibracao real, preservando a
regra central do Fezinha:

```text
Nenhuma camada le output de outra camada. Fusao so acontece no agregador final.
```

Este fallback nao e calibrado por backtest e nao autoriza recomendacao de banca.

## Modos

| Modo | Quando ocorre | Uso na UI |
|---|---|---|
| `nucleo_apenas` | Apenas Dixon-Coles baseline esta disponivel. | Motor parcial. |
| `modelo_only` | Ha sinal interno alem do nucleo, como forca comparativa ou forca real, mas sem odds validas. | Modelo proprio sem odds; sem EV/banca. |
| `fallback_pesos` | Modelo proprio + odds 1X2 validas com fonte minima. | Fusao por pesos fixos; ainda sem calibracao. |

## Fontes fundidas

### Modelo proprio

O sinal interno `modelo_proprio` e montado assim:

| Fonte | Peso interno |
|---|---:|
| `dixon_coles` | 0.75 |
| `forca_comparativa` | 0.25 |

Se `forca_comparativa` nao existir, o modelo proprio usa `dixon_coles: 1.0`.

A forca comparativa produz uma expectativa binaria do mandante. Para converter
para 1X2 sem inventar empate, o agregador preserva o empate do Dixon-Coles e
redistribui o restante entre casa/visitante pela expectativa do mandante.

### Odds

Odds entram somente quando:

- mercado = `1x2`;
- ha selecoes `casa`, `empate`, `visitante`;
- odds sao maiores que 1.0;
- ha pelo menos duas casas validas.

O agregador remove a margem por casa e depois tira a media das probabilidades
sem margem.

### Pesos externos do fallback

O contrato de `layers/agregador.yaml` define:

| Fonte | Peso bruto |
|---|---:|
| `modelo_proprio` | 0.55 |
| `odds` | 0.30 |
| `consenso` | 0.15 |

No v0, `consenso` nao esta ativo. Quando odds validas existem, os pesos sao
renormalizados entre as fontes disponiveis (`modelo_proprio` e `odds`) e
registrados em `agregador.meta.pesos_em_uso`.

## Banca

Mesmo em `fallback_pesos`, o motor retorna:

```json
"banca": {
  "recomendacoes": []
}
```

Motivo: fallback por pesos fixos nao e calibracao. EV, stake e Kelly dependem
de probabilidade calibrada e odds validas. Nesta fase, odds podem ajudar a
explicar/fundir probabilidade, mas nao autorizam stake.

## Payload

O bloco `agregador` segue `contract-engine-api-web-v0.md` e adiciona metadados:

```ts
agregador.meta: {
  modo: "nucleo_apenas" | "modelo_only" | "fallback_pesos"
  camadas_ativas: string[]
  camadas_pendentes: string[]
  pesos_em_uso: Record<string, number>
  pesos_modelo: Record<string, number>
  calibrado: false
  data_ultimo_treino: null
}
```

`indice_confianca.valor` continua `null` ate haver backtest/calibracao.

## Trace

O trace agora registra:

- `odds`: `ok` ou `dado_ausente`;
- `agregador`: `ok`, com modo, pesos e `calibrado: false`;
- `banca`: `pendente`, com `recomendacoes: []`.

## Testes

Arquivo:

- `engine/test_agregador_fallback.py`

Cobertura:

- odds 1X2 com margem removida;
- odds incompletas nao acionam fallback;
- `modelo_only` funde forca comparativa sem gerar banca;
- `fallback_pesos` usa odds validas sem gerar EV/stake.

## Limites

- Nao e stacking.
- Nao e calibrado.
- Nao calcula EV.
- Nao sugere stake.
- Nao usa sites de palpite.
- Nao substitui backtest.
