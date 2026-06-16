---
project: fezinha
author: codex
date: 2026-06-15
kind: manual_observation
status: local_branch_state
topic: codex_contract_v0_deliveries
branch: codex/contract-v0
source_files:
  - docs/spec/contract-engine-api-web-v0.md
  - docs/spec/agregador-fallback-v0.md
  - docs/spec/radar-time-v0.md
  - docs/spec/source-registry-v0.yaml
  - engine/agregador.py
  - engine/radar_time.py
  - engine/ingestion/cbf_tabelas.py
  - engine/ingestion/manual_source_batch.py
---

# Entregas locais do Codex no branch codex/contract-v0

Estado local em 2026-06-15: branch `codex/contract-v0`, sem push feito pelo
Codex nesta etapa.

Entregas principais:

- contrato `engine -> api -> web v0`;
- agregador fallback executavel, sem EV/stake/banca automatica;
- validador de lote manual `manual_source_batch_v0`;
- parser CBF HTML para classificacao, CA/CV agregado e jogos/resultados;
- contrato e produtor local `radar_time_v0`;
- registro operacional de fontes e backlog de fontes candidatas;
- handoff local para Claude.

Commits locais relevantes recentes:

- `da2d780 docs: register source candidates`
- `99ac7c7 fix: clarify radar team identity`

Limites importantes:

- nao ha endpoint real do radar ainda;
- nao ha persistencia/staging do radar no banco;
- nao ha upsert automatico de lote aprovado para producao;
- API-Football, Open-Meteo, SofaScore, FBref, OddsPortal e afins ainda nao estao
  ativos operacionalmente;
- odds nao devem gerar recomendacao de banca sem calibracao/backtest.

Proxima direcao tecnica:

- re-review/merge do PR #1 do Claude;
- PR #2 do Codex: contrato + engine + parser + fontes;
- formalizar endpoints de catalogo de times/partidas;
- criar endpoint de radar por time;
- integrar CA/CV da CBF ao fluxo que acende `controle_disciplinar`.

