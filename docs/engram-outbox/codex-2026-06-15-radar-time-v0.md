---
project: fezinha
author: codex
date: 2026-06-15
kind: manual_observation
status: contract_decision
topic: radar_time_v0
source_files:
  - docs/spec/radar-time-v0.md
  - engine/radar_time.py
  - engine/test_radar_time.py
  - docs/coordination/handoff-claude-2026-06-15.md
---

# Contrato radar_time_v0

O radar de time e elemento explicativo para apoiar a decisao do usuario. Ele nao
alimenta agregador, EV, stake ou recomendacao. Regra central:

Radar explica. Agregador decide.

Eixos MVP:

- `forca_ofensiva`
- `solidez_defensiva`
- `forma_recente`
- `consistencia`
- `contexto_casa_fora`
- `controle_disciplinar`

Estados por eixo:

- `ok`
- `baixa_amostra`
- `dado_ausente`
- `quarentena`
- `conflito`
- `fonte_vencida`

Decisao de identidade:

- `team.id` e `number | null`.
- No produtor puro `engine.radar_time`, `team.id` sai `null`, porque o lote
  manual nao carrega o id canonico do banco.
- `team.slug` e obrigatorio e serve para reconciliar lote manual, catalogo e API.
- A rota web pode continuar numerica: `/times/{team_id}`.
- O endpoint API futuro deve resolver `team_id -> teams.slug`, gerar/buscar o
  radar e devolver `team.id` preenchido.

Escala:

- `eixos[].base` e `eixos[].atual` usam escala 0..100.
- `null` significa ausencia/conflito/quarentena; UI nao deve converter em 50.
- Na v0, `base == atual` e `delta` tende a 0 porque nao ha modificadores.

Validacao local registrada:

- `python -m engine.test_radar_time` passou 2/2 no branch `codex/contract-v0`.

