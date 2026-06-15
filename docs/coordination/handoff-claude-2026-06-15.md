# Handoff para Claude - 2026-06-15

Autor: Codex
Escopo: sincronizacao local entre worktrees `fezinha` e `fezinha-claude`
Status: atualizado

## Resumo curto

O branch Codex `codex/contract-v0` agora tem:

- contrato `engine -> api -> web v0`;
- agregador fallback executavel;
- validador de lote manual `manual_source_batch_v0`;
- parser CBF HTML para classificacao, CA/CV e jogos;
- contrato e processador local `radar_time_v0`;
- registro operacional de CBF e ge.globo;
- avaliacao de fontes futuras: API-Football, Open-Meteo e sites de palpite.

O radar ja tem shape tecnico e processamento local em `engine/radar_time.py`.
Ainda nao existe endpoint API nem persistencia no banco para o radar. A UI pode
seguir com mock/contrato, mas nao deve declarar modo real conectado ao backend.

## Estado local verificado

| Item | Estado |
|---|---|
| Repo Codex | `C:\Users\ianfl\Documents\fezinha` |
| Worktree Claude | `C:\Users\ianfl\Documents\fezinha-claude` |
| Branch Codex | `codex/contract-v0` |
| Branch Claude informado | `claude/web-map` |
| Ultimo commit Codex conhecido | ver `git log` no branch `codex/contract-v0` |
| Push remoto | nao feito |

## Arquivos que Claude deve ler

1. `docs/spec/contract-engine-api-web-v0.md`
2. `docs/spec/agregador-fallback-v0.md`
3. `docs/spec/radar-time-v0.md`
4. `docs/spec/source-catalog-v0.md`
5. `docs/spec/source-registry-v0.yaml`
6. `docs/spec/future-source-evaluation-v0.md`
7. `docs/coordination/source-ingestion-flow-tasks.md`

## Entregas Codex relevantes

### Contrato de analise

- `docs/spec/contract-engine-api-web-v0.md`
- `engine/test_contract_v0.py`
- `engine/run.py`

Define envelope minimo de `POST /queries`, modo operacional, trace, alertas,
banca e forca comparativa explicativa.

### Agregador fallback

- `docs/spec/agregador-fallback-v0.md`
- `engine/agregador.py`
- `engine/test_agregador_fallback.py`
- `api/routers/queries.py`

O motor agora diferencia:

- `nucleo_apenas`: apenas Dixon-Coles baseline;
- `modelo_only`: modelo proprio com forca comparativa/forca real, sem odds;
- `fallback_pesos`: modelo proprio + odds 1X2 validas.

Mesmo em `fallback_pesos`, o backend nao gera EV, stake ou recomendacao de
banca. `banca.recomendacoes` continua vazio porque ainda nao ha calibracao por
backtest.

### Ingestao manual e fonte CBF

- `docs/templates/manual_source_batch_v0.md`
- `docs/templates/manual_source_batch_v0.schema.json`
- `docs/templates/notebooklm-extraction-prompt.md`
- `engine/ingestion/manual_source_batch.py`
- `engine/ingestion/cbf_tabelas.py`
- `engine/test_manual_source_batch.py`
- `engine/test_cbf_tabelas.py`

O parser CBF local consegue gerar lote validado sem escrever no banco. Em teste
com HTML salvo da CBF Serie B, extraiu classificacao, disciplina e jogos.

### Radar por time

- `docs/spec/radar-time-v0.md`
- `engine/radar_time.py`
- `engine/test_radar_time.py`

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

Regra obrigatoria para UI: eixo sem dado usa `null`, apagado/tracejado, nunca
valor neutro inventado como 50.

### Fontes futuras

- API-Football: `futuro`, depende de custo, chave, cobertura Serie A/B 2026 e
  confirmacao real de xG.
- Open-Meteo: `futuro`, depende de catalogo de estadios com latitude/longitude
  e backtest antes de peso no agregador.
- Sites de palpite: `quarentena`, sem uso em agregador, banca ou radar
  numerico sem backtest cego.

## O que Claude pode fazer agora

- Revisar `docs/spec/radar-time-v0.md` como consumidor web.
- Implementar ou ajustar mock do componente de radar usando exatamente o shape
  `radar_time_v0`.
- Renderizar estados de fonte/eixo: `ok`, `baixa_amostra`, `dado_ausente`,
  `quarentena`, `conflito`, `fonte_vencida`.
- Exibir tooltip com fonte, janela, qualidade e `valor_bruto`.
- Usar o mesmo componente para:
  - pagina do time: um radar com `contexto: "geral"`;
  - analise de partida: dois radares sobrepostos, mandante `casa` e visitante
    `fora`.

## O que Claude deve esperar

- Endpoint API real para `radar_time`.
- Persistencia/staging no banco.
- Importacao automatica aprovada para banco.
- Dados pagos de elenco, lesao, escalacao e xG.
- Uso de API-Football, Open-Meteo ou sites de palpite em producao.

## Proximas tarefas Codex

1. Aguardar review do Claude sobre `radar-time-v0`.
2. Se aprovado, criar endpoint API para expor radar por time.
3. Revisar agregador fallback como consumidor web se a UI usar novos modos/metadados.
4. Se o humano aprovar, desenhar/implementar migration de staging B2.
5. Depois de B2, implementar upsert idempotente B3.

## Cuidados de conflito

- Claude deve evitar editar `engine/`, `db/migrations/` e contratos sem abrir
  review.
- Codex deve evitar editar `web/` enquanto o branch `claude/web-map` estiver
  ativo.
- Alteracoes em `docs/spec/` devem ser revisadas pelo outro agente quando
  afetarem contrato.
- Nao fazer push ate ordem humana.

## Nao stagear

- `web/tsconfig.tsbuildinfo`
- `.claude/` se for apenas configuracao local de preview
- `.next/`
- `node_modules/`

## Limites deste handoff

- Agregador fallback esta pronto localmente, mas nao calibrado.
- Nao afirma que radar tem endpoint API.
- Nao afirma que o banco foi populado.
- Nao afirma que API-Football, Open-Meteo ou sites de palpite estao ativos.
- Nao faz push.
