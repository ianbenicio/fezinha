# Tarefas - Fluxo de Ingestao de Fontes

Status: em andamento
Versao: v0
Data: 2026-06-15
Base: `docs/spec/source-catalog-v0.md`

## Objetivo

Desenvolver um fluxo seguro para transformar links, PDFs, HTML, CSVs ou
documentos gerados por ferramentas como NotebookLM em dados utilizaveis pelo
Fezinha, sem gravar valor factual sem fonte e sem permitir que LLM vire fonte
primaria.

Fluxo alvo:

```text
Fonte catalogada
-> snapshot bruto
-> extracao assistida ou parser
-> JSON/CSV normalizado
-> validador local
-> relatorio de divergencia
-> staging/quarentena
-> aprovacao humana ou regra automatica
-> upsert no banco
```

## Principios

- NotebookLM, LLM ou plugin web podem ajudar a extrair e estruturar.
- O valor factual vem da fonte original, nao da ferramenta de extracao.
- Todo lote precisa carregar `source_url`, `fetched_at`, `snapshot/hash` e
  `quality_score`.
- Sem validacao, o dado fica em quarentena.
- Sem odds validas, nao existe EV/stake/banca.
- Sem fonte de jogador, nao existe elenco/lesao/escalacao factual.

## Fase A - Bootstrap assistido manual

Objetivo: permitir alimentar dados iniciais com controle humano, antes da
automacao.

### A1. Template de lote manual

Owner: Codex
Pode editar: `docs/templates/`, `docs/spec/`
Nao pode editar: `db/migrations/`

Tarefas:

- [x] Definir formato padrao `manual_source_batch_v0`.
- [x] Incluir campos obrigatorios de proveniencia.
- [x] Permitir entrada em JSON e CSV.
- [x] Documentar exemplos para classificacao, calendario, resultado, CA/CV,
      noticias e odds.

Criterio de pronto:

- Existe template versionado.
- Campos obrigatorios batem com `source-catalog-v0.md`.
- Lote sem fonte nao passa no schema.

Artefatos:

- `docs/templates/manual_source_batch_v0.md`
- `docs/templates/manual_source_batch_v0.schema.json`
- `docs/templates/manual_source_batch_v0.example.json`

### A2. Prompt padrao para NotebookLM/outra ferramenta

Owner: Codex
Pode editar: `docs/templates/`

Tarefas:

- [x] Criar prompt que exige extrair apenas dados presentes na fonte.
- [x] Exigir `null` quando o dado nao estiver explicitamente na fonte.
- [x] Exigir URL, data de coleta, titulo da fonte e trecho/linha quando
      possivel.
- [x] Proibir completamento por memoria ou inferencia.
- [x] Pedir saida em JSON/CSV compativel com `manual_source_batch_v0`.

Criterio de pronto:

- Prompt pronto para o usuario colar no NotebookLM ou ferramenta equivalente.
- Prompt deixa claro: "nao invente, nao complete, nao estime".

Artefato:

- `docs/templates/notebooklm-extraction-prompt.md`

### A3. Validador local de lote

Owner: Codex
Pode editar: `engine/ingestion/`, `engine/test_*`, `docs/`

Tarefas:

- [x] Criar comando local para validar lote JSON/CSV.
- [x] Checar campos obrigatorios.
- [x] Checar tipos e limites de sanidade.
- [x] Checar duplicidade por chave natural.
- [x] Marcar `ok`, `quarentena`, `conflito` ou `rejeitado`.
- [x] Gerar relatorio legivel antes de qualquer upsert.

Criterio de pronto:

- Lote valido gera relatorio sem escrever no banco por padrao.
- Lote com valor faltante/fonte ausente nao e aceito como fato.
- Testes cobrem caso valido, ausente, conflito e duplicado.

Artefatos:

- `engine/ingestion/manual_source_batch.py`
- `engine/test_manual_source_batch.py`
- `engine/ingestion/README.md`

### A4. Processo humano de aprovacao

Owner: Humano responsavel
Suporte: Codex

Tarefas:

- [ ] Validar com humano: onde o relatorio sera revisado.
- [ ] Validar com humano: quem aprova lote manual.
- [ ] Validar com humano: quando lote pode ir para banco.
- [ ] Validar com humano: regra de rollback se lote aprovado estiver errado.

Criterio de pronto:

- Existe procedimento documentado.
- Nenhum lote manual entra no banco sem decisao explicita.

Artefato proposto:

- `docs/spec/manual-batch-approval-v0.md`

Observacao:

- Codex documentou o procedimento, mas A4 continua pendente ate validacao
  humana explicita.

## Fase B - Staging e banco

Objetivo: separar dado recebido de dado aprovado.

### B1. Desenhar staging/quarentena

Owner: Codex
Pode editar: `docs/spec/`
Revisor obrigatorio: humano

Tarefas:

- [x] Definir se staging sera tabela nova, arquivo local versionado ou pasta de
      lotes processados.
- [x] Definir metadados minimos de lote.
- [x] Definir lifecycle: `recebido`, `validado`, `quarentena`, `aprovado`,
      `importado`, `rejeitado`.
- [x] Definir politica de retencao de snapshot bruto.

Criterio de pronto:

- Decisao documentada antes de migration.

Artefato:

- `docs/spec/manual-ingestion-staging-v0.md`

### B2. Migration de staging, se aprovada

Owner: Codex
Pode editar: `db/migrations/`
Revisor obrigatorio: humano

Tarefas:

- [ ] Criar migration incremental.
- [ ] Registrar lote, fonte, hash, status, payload bruto e relatorio.
- [ ] Nao reescrever migration aplicada.

Criterio de pronto:

- Migration revisada.
- Sem impacto em tabelas de producao sem necessidade.

### B3. Upsert aprovado

Owner: Codex
Pode editar: `engine/ingestion/`, `api/` se necessario

Tarefas:

- [ ] Implementar upsert somente para lote `aprovado`.
- [ ] Preservar source metadata.
- [ ] Nao sobrescrever dado sensivel em conflito.
- [ ] Gerar log de importacao.

Criterio de pronto:

- Upsert e idempotente.
- Conflitos nao sobrescrevem silenciosamente.

## Fase C - Automacao por fonte

Objetivo: trocar fluxo manual por coletor reproduzivel, uma fonte por vez.

### C1. Fonte 1 - CBF Tabelas

Owner: Codex
Pode editar: `engine/ingestion/`, `docs/spec/`

Tarefas:

- [x] Criar registro operacional de fonte `cbf_tabelas`.
- [x] Calcular hash de snapshot local HTML/PDF.
- [x] Automatizar captura/download HTML.
- [x] Extrair classificacao.
- [x] Extrair CA/CV agregado quando disponivel.
- [x] Extrair jogos/resultados quando disponivel.
- [x] Validar contra schema.
- [x] Alimentar radar MVP: ataque, defesa, forma, consistencia, casa/fora e
      disciplina quando CA/CV existir.

Criterio de pronto:

- CBF consegue alimentar dado factual sem NotebookLM.
- Disciplina sai de `dado_ausente` para `ok` apenas quando CA/CV for extraido
  com fonte.

Artefatos parciais:

- `docs/spec/source-registry-v0.yaml`
- `docs/spec/radar-time-v0.md`
- `engine/ingestion/cbf_tabelas.py`
- `engine/radar_time.py`
- `engine/test_cbf_tabelas.py`
- `engine/test_radar_time.py`

Status parcial:

- HTML salvo da CBF Serie B em 2026-06-15 foi parseado com 20 linhas de
  classificacao, 20 registros de disciplina e 10 jogos/resultados da rodada,
  todos validados como lote `manual_source_batch_v0`.
- Entrada por URL ja baixa HTML para snapshot local e calcula hash.
- `engine.radar_time` ja gera payload local `radar_time_v0` a partir do lote
  CBF validado.
- Upsert, endpoint API e review do Claude ainda nao foram feitos.

### C2. Fonte 2 - ge.globo

Owner: Codex
Pode editar: `engine/ingestion/`, `docs/spec/`

Tarefas:

- [x] Formalizar ge.globo no catalogo operacional.
- [x] Revisar campos ja ingeridos.
- [x] Adicionar qualidade/fonte quando possivel.
- [x] Manter noticias como noticia/contexto, nao fato numerico sem validacao.

Criterio de pronto:

- ge.globo segue o mesmo padrao de proveniencia do catalogo.

Artefatos:

- `docs/spec/source-registry-v0.yaml`
- `engine/ingestion/ge_globo.py`
- `engine/test_ge_globo_metadata.py`

Observacao:

- `teams.caracteristicas` recebe `_fontes.ge_globo` para classificacao/forma.
- `news` ja guarda `url`, `fonte` e `coletado_em`.
- `matches` ainda nao tem colunas de proveniencia; CBF segue preferencial para
  dado factual de motor/backtest.

### C3. Fontes futuras

Owner: Codex
Revisor: humano

Tarefas:

- [x] Avaliar API-Football antes de pagar/ligar.
- [x] Avaliar Open-Meteo para clima.
- [x] Manter sites de palpite em quarentena ate prova empirica.

Criterio de pronto:

- Nenhuma fonte nova vira `ativo` sem passar por promocao de fonte.

Artefatos:

- `docs/spec/future-source-evaluation-v0.md`
- `docs/spec/source-registry-v0.yaml`

Observacao:

- API-Football e Open-Meteo ficam `futuro`.
- Sites de palpite ficam `quarentena`.
- Nenhuma dessas fontes foi ligada ao banco ou ao motor.

## Fase D - Exibicao e auditoria

Objetivo: deixar o usuario saber quando dado e real, ausente, vencido ou
aproximado.

### D1. Estados visuais de fonte

Owner: Claude
Pode editar: `web/`
Depende de: contrato de status de fonte

Tarefas:

- [ ] Exibir `ok`, `dado_ausente`, `fonte_vencida`, `quarentena`, `conflito`.
- [ ] Mostrar fonte e janela no tooltip do radar.
- [ ] Mostrar noticias por time como filtro aproximado enquanto nao houver tag
      canonica.

Criterio de pronto:

- UI nao oculta dado ausente.
- UI nao apresenta dado aproximado como fato.

### D2. Painel interno de auditoria

Owner: futuro

Tarefas:

- [ ] Listar fontes ativas e vencidas.
- [ ] Listar lotes em quarentena.
- [ ] Mostrar ultimos conflitos.
- [ ] Mostrar ultima coleta por fonte.

Criterio de pronto:

- Operador consegue identificar fonte quebrada antes de ela contaminar o
  produto.

## Ordem recomendada

1. A1 - Template de lote manual.
2. A2 - Prompt padrao para NotebookLM/outra ferramenta.
3. A3 - Validador local.
4. B1 - Decisao de staging/quarentena.
5. C1 - Automacao CBF Tabelas.
6. D1 - Estados visuais para Claude.

## Fora de escopo por enquanto

- Popular banco de producao automaticamente.
- Usar LLM como fonte factual.
- Coletar redes sociais como fato.
- Automatizar sites de palpite.
- Calcular EV/stake sem odds validadas.
