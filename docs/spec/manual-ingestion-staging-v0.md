# Staging e quarentena para ingestao manual v0

Status: proposto para validacao humana
Versao: v0
Data: 2026-06-15
Base: `docs/templates/manual_source_batch_v0.md`

## Objetivo

Definir como um lote manual ou semi-manual passa de arquivo recebido para dado
aprovado, sem escrever direto nas tabelas finais do Fezinha.

Regra central:

```text
Validar nao e importar. Importar exige aprovacao explicita ou regra automatica
documentada.
```

## Decisao v0

Para o bootstrap, o staging sera baseado em arquivo local + relatorio de
validacao. Nao criaremos migration de staging agora.

Motivos:

- ainda estamos validando quais fontes e formatos chegam melhor;
- os primeiros lotes podem ter erros de estrutura e de fonte;
- criar tabela cedo demais tende a cristalizar campos errados;
- o validador ja produz decisao por registro sem depender do banco;
- o banco de producao nao deve receber dado antes da aprovacao humana.

Migration de staging fica para B2, depois de pelo menos alguns lotes reais
passarem pelo fluxo e revelarem os metadados que precisam persistir.

## Estrutura local recomendada

Os caminhos abaixo sao operacionais. Eles podem existir localmente ou em storage
controlado, mas nao devem ser usados para commitar dados brutos sensiveis no
repo.

```text
var/ingestion/
  received/      # lote recebido como veio da ferramenta/operador
  validated/     # lote que passou sem erro estrutural
  quarantine/    # lote ou registros com duvida, conflito, fonte fraca ou falta de snapshot/hash
  approved/      # lote aprovado por humano para importacao futura
  imported/      # lote ja importado, com log de importacao
  rejected/      # lote rejeitado
  reports/       # relatorios do validador
  snapshots/     # HTML/PDF/CSV bruto ou referencia local
```

Regra: snapshots de HTML/PDF/noticia nao devem ser copiados para o git sem
decisao explicita. Para noticia, preferir URL + hash + trecho curto, nao corpo
integral do artigo.

## Lifecycle

| Status | Origem | Condicao de entrada | Proxima acao |
|---|---|---|---|
| `recebido` | arquivo bruto | operador/ferramenta entregou JSON/CSV/PDF/HTML | rodar validador |
| `validado` | validador | sem erros estruturais | revisao humana |
| `quarentena` | validador ou humano | fonte fraca, ausencia de snapshot/hash, ambiguidade, conflito parcial | corrigir fonte ou manter fora do motor |
| `aprovado` | humano | lote revisado e liberado | upsert futuro |
| `importado` | processo de importacao | upsert executado e logado | manter auditoria |
| `rejeitado` | validador ou humano | sem fonte, erro factual, completamento por inferencia, conflito grave | nao importar |

## Metadados minimos por lote

Todo lote recebido deve ter ou gerar:

| Campo | Uso |
|---|---|
| `batch_id` | rastreio do lote |
| `schema_version` | compatibilidade do validador |
| `created_at` / `created_by` | autoria operacional |
| `source_id` / `source_url` / `source_type` | origem factual |
| `fetched_at` | momento da coleta |
| `source_snapshot_path` ou `raw_payload_hash` | auditabilidade |
| `validator_name` / `validator_version` | reprodutibilidade |
| `git_commit` | versao do codigo que validou |
| `report_path` | relatorio produzido |
| `records_total` | volume do lote |
| `records_ok` | registros candidatos a importacao |
| `records_quarantine` | registros bloqueados para fato |
| `records_conflict` | registros que exigem decisao |
| `records_rejected` | registros invalidos |
| `approved_by` / `approved_at` | aprovacao humana futura |
| `imported_at` / `import_log_path` | rastreio de upsert futuro |

## Regras de movimentacao

1. Todo lote entra em `received/`.
2. O validador gera relatorio em `reports/`.
3. Se houver erro estrutural, o lote vai para `rejected/` ou `quarantine/`.
4. Se nao houver erro, mas houver registros em quarentena/conflito, o lote pode
   ir para `validated/` com bloqueio parcial.
5. Somente humano responsavel move para `approved/`.
6. Processo de importacao futuro so le `approved/`.
7. Importacao move uma copia auditavel para `imported/` com log.
8. Nenhum processo sobrescreve arquivo original; novos arquivos recebem novo
   `batch_id` ou sufixo de revisao.

## Politica de retencao

| Artefato | Retencao v0 | Observacao |
|---|---|---|
| lote JSON/CSV recebido | manter enquanto a temporada estiver em uso | necessario para auditoria |
| relatorio de validacao | manter junto do lote | explica decisao |
| snapshot CBF/PDF/HTML oficial | manter localmente enquanto alimentar backtest/modelo | nao commitar por padrao |
| noticia completa | nao armazenar corpo integral por padrao | usar URL, hash e trecho curto |
| odds manuais | manter lote e timestamp | necessario para EV/backtest futuro |
| arquivo rejeitado | manter ate encerrar revisao do ciclo | depois pode arquivar/remover |

## Criterios para criar migration B2

Nao criar migration de staging ate que estes pontos estejam resolvidos:

- pelo menos um lote real CBF validado de ponta a ponta;
- pelo menos um lote com erro/quarentena revisado;
- campos obrigatorios do lote confirmados na pratica;
- decisao humana sobre guardar payload bruto no banco ou apenas hash/path;
- politica de privacidade/licenca de snapshots aceita;
- desenho de upsert idempotente definido.

Quando estes criterios passarem, a migration B2 deve criar tabelas ou estrutura
equivalente para:

- registrar lote;
- registrar fonte;
- guardar hash/path do payload bruto;
- guardar relatorio;
- guardar status por registro;
- bloquear importacao sem aprovacao.

## Impacto no Claude/web

Claude nao depende desta decisao para UI mockada. No futuro, a UI pode receber
os status `ok`, `dado_ausente`, `quarentena`, `conflito` e `fonte_vencida` para
mostrar estado de fonte ao usuario.

