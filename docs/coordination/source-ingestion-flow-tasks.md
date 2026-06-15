# Tarefas - Fluxo de Ingestao de Fontes

Status: planejado
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

- [ ] Definir formato padrao `manual_source_batch_v0`.
- [ ] Incluir campos obrigatorios de proveniencia.
- [ ] Permitir entrada em JSON e CSV.
- [ ] Documentar exemplos para classificacao, calendario, resultado, CA/CV,
      noticias e odds.

Criterio de pronto:

- Existe template versionado.
- Campos obrigatorios batem com `source-catalog-v0.md`.
- Lote sem fonte nao passa no schema.

### A2. Prompt padrao para NotebookLM/outra ferramenta

Owner: Codex
Pode editar: `docs/templates/`

Tarefas:

- [ ] Criar prompt que exige extrair apenas dados presentes na fonte.
- [ ] Exigir `null` quando o dado nao estiver explicitamente na fonte.
- [ ] Exigir URL, data de coleta, titulo da fonte e trecho/linha quando
      possivel.
- [ ] Proibir completamento por memoria ou inferencia.
- [ ] Pedir saida em JSON/CSV compativel com `manual_source_batch_v0`.

Criterio de pronto:

- Prompt pronto para o usuario colar no NotebookLM ou ferramenta equivalente.
- Prompt deixa claro: "nao invente, nao complete, nao estime".

### A3. Validador local de lote

Owner: Codex
Pode editar: `engine/ingestion/`, `engine/test_*`, `docs/`

Tarefas:

- [ ] Criar comando local para validar lote JSON/CSV.
- [ ] Checar campos obrigatorios.
- [ ] Checar tipos e limites de sanidade.
- [ ] Checar duplicidade por chave natural.
- [ ] Marcar `ok`, `quarentena`, `conflito` ou `rejeitado`.
- [ ] Gerar relatorio legivel antes de qualquer upsert.

Criterio de pronto:

- Lote valido gera relatorio sem escrever no banco por padrao.
- Lote com valor faltante/fonte ausente nao e aceito como fato.
- Testes cobrem caso valido, ausente, conflito e duplicado.

### A4. Processo humano de aprovacao

Owner: Humano responsavel
Suporte: Codex

Tarefas:

- [ ] Definir onde o relatorio sera revisado.
- [ ] Definir quem aprova lote manual.
- [ ] Definir quando lote pode ir para banco.
- [ ] Definir regra de rollback se lote aprovado estiver errado.

Criterio de pronto:

- Existe procedimento documentado.
- Nenhum lote manual entra no banco sem decisao explicita.

## Fase B - Staging e banco

Objetivo: separar dado recebido de dado aprovado.

### B1. Desenhar staging/quarentena

Owner: Codex
Pode editar: `docs/spec/`
Revisor obrigatorio: humano

Tarefas:

- [ ] Definir se staging sera tabela nova, arquivo local versionado ou pasta de
      lotes processados.
- [ ] Definir metadados minimos de lote.
- [ ] Definir lifecycle: `recebido`, `validado`, `quarentena`, `aprovado`,
      `importado`, `rejeitado`.
- [ ] Definir politica de retencao de snapshot bruto.

Criterio de pronto:

- Decisao documentada antes de migration.

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

- [ ] Criar registro operacional de fonte `cbf_tabelas`.
- [ ] Capturar HTML/PDF e salvar snapshot/hash.
- [ ] Extrair classificacao.
- [ ] Extrair CA/CV agregado quando disponivel.
- [ ] Extrair jogos/resultados quando disponivel.
- [ ] Validar contra schema.
- [ ] Alimentar radar MVP: ataque, defesa, forma, consistencia, casa/fora e
      disciplina quando CA/CV existir.

Criterio de pronto:

- CBF consegue alimentar dado factual sem NotebookLM.
- Disciplina sai de `dado_ausente` para `ok` apenas quando CA/CV for extraido
  com fonte.

### C2. Fonte 2 - ge.globo

Owner: Codex
Pode editar: `engine/ingestion/`, `docs/spec/`

Tarefas:

- [ ] Formalizar ge.globo no catalogo operacional.
- [ ] Revisar campos ja ingeridos.
- [ ] Adicionar qualidade/fonte quando possivel.
- [ ] Manter noticias como noticia/contexto, nao fato numerico sem validacao.

Criterio de pronto:

- ge.globo segue o mesmo padrao de proveniencia do catalogo.

### C3. Fontes futuras

Owner: Codex
Revisor: humano

Tarefas:

- [ ] Avaliar API-Football antes de pagar/ligar.
- [ ] Avaliar Open-Meteo para clima.
- [ ] Manter sites de palpite em quarentena ate prova empirica.

Criterio de pronto:

- Nenhuma fonte nova vira `ativo` sem passar por promocao de fonte.

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
