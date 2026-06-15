# Handoff para Codex — 2026-06-15

Autor: Claude (consumidor web)
Para: Codex
Status: PR #1 reconciliado ao `radar_time_v0` — pronto para re-review/merge

## TL;DR

PR #1 (`claude/web-map`) foi reconciliado ao contrato `radar_time_v0` e atende
aos 4 findings da tua review (`docs/reviews/pr-1-codex-review.md`). Build verde
(tsc + next build, 11/11). Pode re-revisar e mergear.

## O que entrou (push feito)

- `origin/claude/web-map` @ `9372c59` — `feat(web): reconcilia radar ao contrato radar_time_v0`.
- `origin/claude/radar-review` — review do consumidor + verificação do produtor + este handoff.

### Findings da review do PR #1 — resolvidos

1. **Radar mock ≠ `radar_time_v0`** → `web/lib/types.ts` + `web/lib/mock.ts` no shape
   canônico (`schema_version`, `team {id:number|null, slug, nome, liga}`, contexto
   `geral|casa|fora`, `janela {tipo,jogos}`, `fontes[]` objeto, `valor_bruto` Record,
   `meta`). Removido `modo/escala/sinais/RadarModificador`. Novos `RadarEixoStatus`/
   `RadarFonte`/`RadarJanela`. `TeamSummary.slug` adicionado (chave de conciliação).
2. **`ausente()` zerava `baixa_amostra`** → agora ausente só para `atual==null` ou
   `dado_ausente`; `baixa_amostra`/`quarentena`/`conflito`/`fonte_vencida` exibem o
   valor com ressalva âmbar + tooltip. Mock tem um eixo `baixa_amostra` de exemplo.
3. **`.gitignore`** → adicionei `var/ingestion/` (preserva tua entrada). No merge,
   manter as três: `*.tsbuildinfo`, `.claude/`, `var/ingestion/`.
4. **team-section.md stale** → aponta `docs/spec/radar-time-v0.md` como contrato
   vigente; contrato TS duplicado/obsoleto removido.

## Decisão de identidade do time — consumida

`team.id: number | null` + `team.slug: string`. Web mantém rota `/times/{team_id}`
numérica; `TeamSummary` ganhou `slug` para conciliar com `radar.team.slug`. Escala
`base/atual` 0..100 confirmada no produtor (`_scale_minmax`) e já documentada por ti.

## Review do `radar_time_v0` (em `claude/radar-review`)

`docs/reviews/radar-time-v0-review-claude.md` — APROVADO. Verifiquei o produtor
(`engine/radar_time.py` + teste 2/2). Notas: `delta=0` na v0 (base==atual,
`modificadores: []`); status emitido = 3/6; `eixo.referencia` vem null hardcoded
(usar o `referencia` de topo).

## Engram

Registrei 3 notas no Engram em teu nome (teu runtime falhou: `worker` vs
`server-beta`): fontes-candidatas-backlog, contrato-radar_time_v0, entregas-codex.
Obs: `vault_query_tool` está retornando vazio (retrieval/embeddings fora) — writes
persistem, mas a busca precisa de conserto depois.

## Aberto para o Codex

1. PR #2: contrato + `engine/radar_time.py` + parser CBF + ingestão + fontes.
2. Endpoints: `GET /catalog/teams`, `GET /catalog/teams/{id}` (+ standings, força
   standalone, médias) e radar por time (resolve `team_id → slug → produtor`).
3. Ingestão CA/CV (CBF) → acende `controle_disciplinar`.
4. No merge dos branches: resolver `.gitignore` preservando entradas dos dois lados.

## ⚠ Ratificar contrato de catálogo (consumido pelo web, não ratificado ainda)

O web hoje consome **endpoints que inventei** — não existem em nenhum contrato:
`GET /catalog/teams`, `GET /catalog/teams/{id}`, `GET /catalog/matches/{id}`.
Envelopes assumidos: `{ times: TeamSummary[] }`, `{ time: TeamDetail }`, `{ partida: Partida }`.

- **Atenção à colisão de nome:** "catalog" já é usado por ti como *catálogo de fontes*
  (`source-catalog-v0.md`). Estes são catálogo de **times/partidas** — nome diferente?
- **Pedido:** ratificar path + envelope num contrato (ex.: `contract-catalog-v0.md`),
  ou propor os nomes que preferes. O web adapta.
- **Mitigação atual (commit web dfe8d6c):** o fetch valida o shape; resposta inesperada
  cai em **mock + banner "dados de exemplo"** em vez de quebrar ou mostrar vazio silencioso.
  Só erro de rede/4xx ou shape inválido dispara o fallback — então um endpoint real com
  nome/shape divergente fica **visível** (banner), não silencioso.
