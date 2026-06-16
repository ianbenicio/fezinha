---
project: fezinha
author: codex
date: 2026-06-15
kind: manual_observation
status: candidate
topic: source_registry
source_files:
  - docs/spec/source-candidates-2026-06-15.md
  - docs/spec/source-registry-v0.yaml
  - docs/spec/source-catalog-v0.md
---

# Fontes candidatas para o Fezinha

O usuario forneceu uma lista de fontes para estruturar o pipeline futuro de
dados do Fezinha. A decisao Codex registrada localmente: todas entram como
candidatas ou quarentena ate validacao objetiva.

Fontes citadas:

- The Odds API
- OddsPortal
- Bet365
- Transfermarkt BR
- oGol
- FootStats
- FBref
- SofaScore
- WhoScored
- ESPN Brasil
- UOL Esporte
- Footure
- ge.globo
- CBF

Regra adotada:

- dado factual nao pode vir de memoria de LLM;
- sem URL/fonte verificavel, nao entra no banco;
- sem termos de uso, cobertura Serie A/B 2026, campos definidos, parser/API ou
  batch manual validado, nao vira fonte operacional;
- sempre guardar `source_url`, `fetched_at`, snapshot/hash quando aplicavel,
  qualidade e metodo de extracao;
- noticias/editorial entram como contexto separado, nao como probabilidade;
- odds nao geram banca/stake sem calibracao e backtest.

Uso atual:

- CBF e ge.globo continuam como fontes reais ja mapeadas no projeto.
- The Odds API e candidata principal para automacao futura de odds.
- SofaScore/FBref/WhoScored sao candidatos para performance por jogo, ainda sem
  validacao de cobertura/termos.
- Transfermarkt e estrutural mensal; nao substitui escalacao confirmada.
- ESPN/UOL/Footure sao contexto/editorial; nao alimentam motor numerico sem
  regra e validacao.

