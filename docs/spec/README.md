# Especificacao do Fezinha

## Estrutura

- `contract-engine-api-web-v0.md` - contrato minimo e retrocompativel entre motor, API e web.
- `radar-time-v0.md` - contrato do radar explicativo por time, fora do agregador.
- `source-catalog-v0.md` - criterios para avaliar sites/fontes e definir uso no banco, motor e UI.
- `source-registry-v0.yaml` - registro operacional inicial de fontes e parsers.
- `manual-ingestion-staging-v0.md` - decisao B1 de staging/quarentena antes de migration.
- `../templates/manual_source_batch_v0.md` - formato para lotes manuais/assistidos antes da validacao.
- `../templates/notebooklm-extraction-prompt.md` - prompt operacional para extracao sem inferencia.
- `secoes-28-35-upgrades.md` - mudancas de design recomendadas para a v3 da arquitetura.
- `secao-36-propriedades-camadas.md` - propriedades obrigatorias para contratos de camada.

## Fluxo de Integracao

1. Documento mestre original: mantido fora do repo por estar em evolucao.
2. Secoes 1-27: arquitetura base, versao 2.0.
3. Secoes 28-35 (`secoes-28-35-upgrades.md`): upgrades v3.
4. Catalogo de fontes (`source-catalog-v0.md`): regra de entrada de dados antes de nova ingestao.
5. Template manual (`../templates/manual_source_batch_v0.md`): contrato de transporte para lotes JSON/CSV.
6. Staging manual (`manual-ingestion-staging-v0.md`): decisao de quarentena local antes de migration.
7. Registry operacional (`source-registry-v0.yaml`): fontes candidatas ligadas a parsers.
8. Radar por time (`radar-time-v0.md`): payload explicativo para pagina de time e confronto.

## Upgrades v3

- Secao 28: revisao do nucleo estatistico.
  - Troca Elo -> pi-ratings.
  - Dixon-Coles com requisitos: rho, xi, blend xG.
  - Remocao de variaveis redundantes.
  - Shrinkage bayesiano.
- Secao 29: agregador otimizado.
  - Stacking multinomial logit.
  - Calibracao isotonica.
  - Validacao walk-forward.
- Secao 30: Moneyball - impacto individual.
  - Metodologia above replacement.
  - Metricas: xG+xA nivel 1 -> xT nivel 2 -> VAEP nivel 3.
  - Pipeline escalacao -> ajuste Dixon-Coles.
- Secoes 31-34: quatro camadas novas.
  - H2H: historico direto, peso baixo, em prova.
  - Fatos relevantes: qualitativo, ajusta incerteza.
  - Visao das casas: sinal editorial, sem odds.
  - Visao do time: antecipado vs consumido.
- Secao 35: arquitetura consolidada v3.

## Regra de Ouro

Nenhuma camada le output de outra. Cada camada produz seus numeros/sinais
independentemente. Fusao acontece so no agregador final.

## Regras de Fontes

Antes de inserir dado novo, criar scraper novo ou automatizar fonte nova:

1. consultar `source-catalog-v0.md`;
2. definir tipo da fonte;
3. definir tipos de dado permitidos;
4. registrar confiabilidade e status operacional;
5. garantir proveniencia, snapshot ou hash do payload;
6. decidir explicitamente se o dado pode ir para banco, UI, radar, motor,
   agregador, banca ou apenas quarentena.

## Proximos Passos

1. Validar `contract-engine-api-web-v0.md` com o consumidor web.
2. Seguir `source-catalog-v0.md` antes de ingerir ou automatizar novas fontes.
3. Implementar agregador fallback sem quebrar o contrato v0.
4. Integrar secoes 28-35 ao documento mestre.
5. Implementar cada componente novo.
6. Coletar historico de previsoes para treinar stacking.
7. Rodar validacao walk-forward e backtest.

---

Versao: 3.1
Data: 2026-06-15
