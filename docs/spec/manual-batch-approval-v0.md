# Aprovacao de lote manual v0

Status: proposto para validacao humana
Versao: v0
Data: 2026-06-15
Base:

- `docs/templates/manual_source_batch_v0.md`
- `docs/spec/manual-ingestion-staging-v0.md`

## Objetivo

Definir quando um lote manual, extraido por NotebookLM, plugin web, parser
local ou operador humano, pode sair de validado/quarentena e virar candidato a
importacao no banco.

Regra central:

```text
Lote validado ainda nao e lote aprovado. Banco so recebe dado com aprovacao
explicita e trilha de auditoria.
```

## Onde revisar

Enquanto B2 nao existir, a revisao acontece fora do banco:

```text
var/ingestion/
  received/
  validated/
  quarantine/
  approved/
  rejected/
  reports/
  snapshots/
```

O revisor deve abrir:

1. lote original em `received/` ou `validated/`;
2. relatorio do validador em `reports/`;
3. snapshot/hash ou URL original da fonte;
4. diff entre revisoes, se o lote tiver sido corrigido.

Snapshots e dados brutos continuam fora do git por padrao.

## Quem aprova

Na fase manual, o aprovador e o humano responsavel pelo projeto Fezinha.

Uma aprovacao valida precisa registrar:

- `batch_id`;
- nome do aprovador;
- data/hora;
- decisao: `aprovado`, `aprovado_parcial`, `rejeitado`;
- registros liberados;
- registros bloqueados;
- justificativa curta;
- commit do codigo do validador usado;
- caminho do relatorio.

Sem esse registro, o lote nao deve ir para `approved/` nem para banco.

## Regras de aprovacao

Um lote pode ser aprovado quando todos os pontos abaixo forem verdadeiros:

- `schema_version` e compativel com o validador atual;
- todos os registros factuais tem `source_url`, `fetched_at` e fonte
  identificavel;
- existe snapshot ou hash do payload bruto quando a fonte permitir;
- nao ha registros com status `rejeitado`;
- registros `conflito` foram resolvidos ou excluidos da importacao;
- registros `quarentena` continuam fora do motor e do banco factual;
- limites de sanidade passaram;
- fonte esta no `source-registry-v0.yaml` como `ativo`, `manual_controlado` ou
  equivalente aprovado;
- o lote nao depende de valor inferido por LLM.

## Aprovacao parcial

Se o lote misturar registros bons e ruins:

- registros `ok` podem ser aprovados;
- registros `quarentena`, `conflito` e `rejeitado` ficam bloqueados;
- o relatorio deve listar exatamente quais `record_id` ou chaves naturais foram
  aprovados;
- o importador futuro deve importar somente os registros liberados.

## Quando pode ir para banco

Antes da migration B2:

- nao deve haver upsert automatico em producao;
- qualquer carga no banco deve ser manual, excepcional e registrada no
  relatorio do lote;
- o caminho preferido e manter os dados em arquivo validado ate B2/B3.

Depois da migration B2:

- somente lote com status `aprovado` ou `aprovado_parcial` pode ser lido pelo
  importador;
- importacao precisa gerar `import_log`;
- upsert deve ser idempotente;
- conflito nunca sobrescreve dado existente silenciosamente.

## Rollback

Antes da migration B2, rollback e operacional e manual:

1. bloquear novos usos do lote;
2. mover copia auditavel para `rejected/` ou `quarantine/`;
3. registrar motivo;
4. criar lote corretivo com novo `batch_id`;
5. se algum dado ja foi inserido manualmente no banco, documentar tabela, chave
   natural, valor antigo, valor novo e responsavel pela correcao.

Depois da migration B2, rollback deve ser por `batch_id`:

- marcar lote como `revertido` ou `substituido`;
- preservar historico;
- aplicar lote corretivo;
- nunca apagar trilha de auditoria.

## Gate para B2

Antes de criar migration de staging, o projeto precisa revisar esta decisao:

- o humano aceita o fluxo de aprovacao;
- pelo menos um lote CBF real foi validado;
- pelo menos um caso de quarentena/conflito foi revisado;
- foi decidido se payload bruto fica no banco ou so hash/path;
- foi definido quem pode executar importacao.

## Limites

- Este documento nao aprova nenhum lote.
- Este documento nao autoriza upsert no banco.
- Este documento nao substitui review humano.
- Este documento nao transforma LLM em fonte factual.
