# Contrato radar_time v0

Status: proposto para review do Claude
Versao: v0
Data: 2026-06-15
Produtor: `engine.radar_time`
Consumidores previstos: pagina de time e analise de partida

## Objetivo

O `radar_time` e um painel explicativo por time. Ele ajuda o usuario a enxergar
forcas e fragilidades, mas nao substitui o agregador e nao altera probabilidade,
EV, stake ou recomendacao.

Regra central:

```text
Radar explica. Agregador decide. Um nao alimenta o outro.
```

## Eixos MVP

| Eixo | Fonte MVP | Regra |
|---|---|---|
| `forca_ofensiva` | CBF classificacao/resultados | gols pro por jogo, normalizado na liga |
| `solidez_defensiva` | CBF classificacao/resultados | gols contra por jogo, invertido e normalizado |
| `forma_recente` | CBF resultados | pontos nos ultimos ate 5 jogos |
| `consistencia` | CBF resultados | estabilidade do saldo de gols recente |
| `contexto_casa_fora` | CBF resultados | pontos no contexto `geral`, `casa` ou `fora` |
| `controle_disciplinar` | CBF CA/CV agregado | CA + 3*CV por jogo, invertido e normalizado |

## Status por eixo

| Status | Significado |
|---|---|
| `ok` | dado suficiente e fonte valida |
| `baixa_amostra` | calculado, mas com poucos jogos |
| `dado_ausente` | fonte ou amostra insuficiente; `base` e `atual` ficam `null` |
| `quarentena` | dado existe, mas nao foi aprovado |
| `conflito` | fontes divergem |
| `fonte_vencida` | coleta antiga demais |

## Payload

```ts
radar_time: {
  schema_version: "radar_time_v0"
  team: {
    id: string
    nome: string
    liga: string
  }
  referencia: {
    liga: string
    temporada: number
    rodada: number
  }
  contexto: "geral" | "casa" | "fora"
  eixos: {
    id: string
    label: string
    base: number | null
    atual: number | null
    delta: number | null
    qualidade: number
    status: "ok" | "baixa_amostra" | "dado_ausente" | "quarentena" | "conflito" | "fonte_vencida"
    janela: {
      tipo: string
      jogos: number
    }
    referencia: {
      liga: string | null
      temporada: number | null
    }
    fontes: {
      source_id: string
      source_url: string
      fetched_at: string
      quality_score: number
      status_fonte: string
    }[]
    valor_bruto: Record<string, unknown>
    modificadores: unknown[]
    motivo_ausencia?: string | null
  }[]
  meta: {
    uso: "explicativo"
    entra_no_agregador: false
    fonte_base: string
    fetched_at: string
  }
}
```

## Uso na UI

- Pagina do time: usar `contexto: "geral"`.
- Analise de partida: gerar um radar do mandante com `contexto: "casa"` e do
  visitante com `contexto: "fora"`.
- Eixo `dado_ausente`: renderizar apagado/tracejado, sem inventar valor 50.
- Eixo `baixa_amostra`: renderizar com aviso de amostra pequena.
- Tooltip deve mostrar fonte, janela, qualidade e `valor_bruto`.

## Estado atual

Implementado:

- processamento local em `engine/radar_time.py`;
- entrada por lote `manual_source_batch_v0`;
- eixos de classificacao, resultados e disciplina;
- testes em `engine/test_radar_time.py`.

Ainda pendente:

- endpoint API para expor radar por time;
- persistencia/staging no banco;
- review do Claude como consumidor web.

