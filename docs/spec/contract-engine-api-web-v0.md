# Contrato engine -> api -> web v0

Status: proposto
Versao: v0
Data: 2026-06-15
Produtor: `engine.analisar_partida`
Transporte: `POST /queries`
Consumidor principal: `web/app/consulta/[matchId]/page.tsx`
Revisor consumidor: Claude Code

## 1. Objetivo

Este contrato congela o shape minimo do payload de analise de partida para a
Fase 1A do Fezinha.

Ele nao declara que o agregador real esta pronto. Ele apenas define a fronteira
retrocompativel entre motor, API e web para que o produto mostre corretamente:

- previsao atual do nucleo estatistico;
- modo operacional do motor;
- forca comparativa como leitura explicativa;
- confianca, alertas, banca e trace sem inventar dado ausente.

Regra central preservada:

```text
Nenhuma camada le output de outra camada. Fusao so acontece no agregador final.
```

## 2. Envelope da API

`POST /queries` deve retornar:

```json
{
  "query_id": 123,
  "custo_creditos": 1,
  "resultado": {}
}
```

`resultado` segue o schema descrito abaixo.

## 3. Resultado

Campos de topo:

| Campo | Tipo | Obrigatorio | Observacao |
|---|---|---:|---|
| `_stub` | boolean | sim | `false` quando vem do motor real. |
| `fonte` | string | sim | Ex.: `nucleo_estatistico_dixon_coles`. |
| `baseline` | boolean | sim | `true` quando falta forca individual dos times. |
| `complexidade` | string | sim | Ecoa a complexidade solicitada. |
| `mercados` | string[] | sim | Mercados solicitados/plano de consulta. |
| `partida` | object | sim | Nomes exibiveis. |
| `lambdas` | object | sim | Diagnostico do nucleo estatistico. |
| `agregador` | object | sim | Bloco retrocompativel de probabilidades exibidas. |
| `forca_comparativa` | object|null | sim | Leitura explicativa nesta fase. |
| `indice_confianca` | object | sim | Pode ter `valor: null`. |
| `alertas` | object[] | sim | Lista vazia permitida. |
| `banca` | object | sim | Sem odds validas, nao gera recomendacao. |
| `trace` | object[] | sim | Log de camadas e estados. |

### 3.1 Partida

```ts
partida: {
  mandante: string
  visitante: string
}
```

### 3.2 Lambdas

```ts
lambdas: {
  casa: number
  fora: number
  escanteios: number
}
```

`lambdas` e diagnostico, nao e recomendacao de aposta.

## 4. Agregador

O bloco `agregador` precisa ser retrocompativel com o web atual. Campos
existentes nao devem ser removidos nem renomeados.

```ts
agregador: {
  modo: "nucleo_apenas" | "modelo_only" | "fallback_pesos"
  resultado: {
    prob_casa: number
    prob_empate: number
    prob_visitante: number
    resultado_mais_provavel: "casa" | "empate" | "visitante" | string
    placar_provavel: string
    top3_placares?: unknown[]
  }
  gols: {
    over_05?: number
    over_15: number
    over_25: number
    over_35: number
    btts: number
  }
  escanteios: {
    over_85: number
    over_95: number
    over_105: number
  }
  meta: {
    modo: "nucleo_apenas" | "modelo_only" | "fallback_pesos"
    camadas_ativas: string[]
    camadas_pendentes: string[]
    pesos_em_uso?: Record<string, number>
    data_ultimo_treino?: string | null
  }
}
```

### 4.1 Modo

`agregador.modo` e a fonte canonica do modo operacional para o web.
`agregador.meta.modo` permanece no payload por retrocompatibilidade e deve ter
o mesmo valor.

Valores:

| Valor | Uso | O que a UI deve dizer |
|---|---|---|
| `nucleo_apenas` | Nucleo estatistico sem forca individual suficiente ou sem fusao. | Motor parcial. Sem contexto, odds ou calibracao completa. |
| `modelo_only` | Modelo proprio com sinais internos, mas sem odds validas. | Sem odds: sem EV/banca. |
| `fallback_pesos` | Fase futura: fusao por pesos fixos documentados. | Fusao fallback, ainda sem stacking treinado. |

Observacao: o nome `nucleo_apenas` preserva o output atual do motor. Nao usar
`nucleo_only` no payload.

## 5. Forca comparativa

Na Fase 1A, `forca_comparativa` e explicativa. Ela nao e a probabilidade final
do resultado e nao deve competir visualmente com `agregador.resultado`.

```ts
forca_comparativa: null | {
  mandante: { ifc: number; leitura: string }
  visitante: { ifc: number; leitura: string }
  diferenca_ifc: number
  expectativa_mandante: number
  leitura: string
  adversarios_comuns: {
    adversario: string
    resultado_mandante: string
    resultado_visitante: string
  }[]
  ajustes_aplicados?: string[]
  jogos_no_grafo: number
}
```

Regra de exibicao:

- `agregador.resultado` e a probabilidade exibida como previsao principal;
- `forca_comparativa.expectativa_mandante` e leitura alternativa/explicativa;
- a fusao da forca comparativa no resultado so deve ocorrer no agregador
  fallback/real, em tarefa posterior e com teste explicito.

## 6. Indice de confianca

```ts
indice_confianca: {
  valor: number | null
  leitura: string
}
```

Enquanto o agregador calibrado nao existir, `valor` pode ser `null`.

## 7. Alertas

```ts
alertas: {
  tipo: string
  descricao: string
  severidade?: "info" | "aviso" | "bloqueio"
}[]
```

Alertas nao alteram probabilidade por conta propria. Eles explicam estado,
risco ou bloqueio operacional.

## 8. Banca

```ts
banca: {
  perfil_em_uso: string
  recomendacoes: {
    mercado: string
    selecao: string
    prob_modelo: number
    odd: number
    ev: number
    stake_sugerido: number
    confianca: number
    decisao: "apostar" | "evitar" | "aguardar_escalacao" | string
  }[]
  nota?: string
}
```

Regra:

- sem odds validas, `recomendacoes` deve ser `[]`;
- sem probabilidade calibrada, a banca deve explicar indisponibilidade;
- nao gerar EV, stake ou recomendacao por suposicao.

## 9. Trace

```ts
trace: {
  camada: string
  topico: string
  status: "ok" | "baseline" | "pendente" | "dado_ausente" | "fonte_vencida" | "erro"
  resumo?: string
  justificativa?: string
  fonte?: string
  fonte_ausente?: string
  entrada: unknown
  saida: unknown
  qualidade?: number
}[]
```

`qualidade`, quando presente, deve estar no intervalo `0..5`.

Para o payload atual, os status existentes (`ok`, `baseline`, `pendente`) sao
suficientes. Os demais valores ficam reservados para ingestao e estados de
fonte.

## 10. Gate de aceite

Antes de considerar a Fase 1A pronta:

- o payload atual do motor passa no teste de shape v0;
- `agregador.resultado/gols/escanteios` permanece retrocompativel;
- `agregador.meta.modo` existe e usa `nucleo_apenas`, `modelo_only` ou
  `fallback_pesos`;
- `indice_confianca`, `alertas`, `banca` e `trace` existem;
- `forca_comparativa` esta documentada como explicativa nesta fase;
- Claude revisa este contrato como consumidor web.
