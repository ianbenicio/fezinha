---
project: fezinha
author: codex
date: 2026-06-15
kind: manual_observation
status: open_decision
topic: catalog_endpoints_pr2
source_files:
  - api/routers/catalog.py
  - docs/spec/radar-time-v0.md
  - docs/coordination/handoff-claude-2026-06-15.md
  - claude/radar-review:docs/coordination/handoff-codex-2026-06-15.md
---

# Decisao aberta para PR #2: catalogo de times/partidas

Claude informou que o web consome endpoints de catalogo de times/partidas que
precisam de contrato ratificado. O nome "catalog" ja existe no projeto tambem
como catalogo de fontes (`source-catalog-v0.md`), entao ha risco de ambiguidade
conceitual.

Endpoints hoje existentes em `api/routers/catalog.py`:

- `GET /catalog/teams`
- `GET /catalog/teams/{team_id}`
- `GET /catalog/news`
- `GET /catalog/matches/{match_id}`
- `GET /catalog/matches`

Necessidade do PR #2:

- criar contrato formal para catalogo operacional de times/partidas;
- definir se o nome continua `/catalog/*` ou muda para evitar colisao com
  catalogo de fontes;
- documentar envelopes de resposta;
- garantir que `GET /catalog/teams` exponha `id`, `slug`, nome, liga e campos
  suficientes para a UI;
- garantir que `GET /catalog/teams/{id}` possa expor detalhe, standings, forma,
  medias e radar futuro;
- criar endpoint de radar por time que resolva `team_id -> slug`;
- preservar fallback honesto no web: shape inesperado deve cair em mock com
  banner de dados de exemplo, nao em silencio.

Decisao tecnica inicial Codex:

- manter `teams.id` como identidade canonica de rota e banco;
- manter `teams.slug` como chave de conciliacao com lote manual e fontes;
- `radar_time.team.id` vem preenchido apenas quando a API enriquecer o payload;
- o produtor engine isolado nao deve inventar id numerico.

