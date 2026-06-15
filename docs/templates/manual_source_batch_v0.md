# Template manual_source_batch_v0

Status: ativo para bootstrap manual
Versao: v0
Data: 2026-06-15
Base: `docs/spec/source-catalog-v0.md`

## Objetivo

Padronizar lotes manuais ou semi-manuais vindos de URL, PDF, HTML, CSV,
planilha, NotebookLM ou outra ferramenta de extracao.

Regra central:

```text
O lote descreve o que a fonte diz. Ele nao cria fato sem fonte.
```

## Formatos aceitos

- JSON canonico: preferido para ingestao e validacao.
- CSV controlado: aceito para bootstrap, desde que tenha as colunas
  obrigatorias e um `payload_json` por linha.

O schema JSON fica em:

```text
docs/templates/manual_source_batch_v0.schema.json
```

Exemplo completo:

```text
docs/templates/manual_source_batch_v0.example.json
```

## Campos obrigatorios do lote

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | string | Deve ser `manual_source_batch_v0`. |
| `batch_id` | string | Id unico do lote. Ex: `cbf-serie-a-2026-r19-20260615`. |
| `created_at` | datetime ISO | Quando o lote foi montado. |
| `created_by` | string | Humano ou ferramenta que montou o lote. |
| `source` | object | Fonte primaria do lote. |
| `records` | array | Lista de registros factuais ou contextuais. |

## Campos obrigatorios da fonte

| Campo | Tipo | Regra |
|---|---|---|
| `source_id` | string | Id catalogado. Ex: `cbf_tabelas`. |
| `source_name` | string | Nome legivel da fonte. |
| `source_url` | string | URL original, nao URL da ferramenta de extracao. |
| `source_type` | enum | Conforme `source-catalog-v0.md`. |
| `fetched_at` | datetime ISO | Quando a fonte foi acessada/coletada. |
| `quality_score` | number | 0 a 5, conforme catalogo de fontes. |
| `status_fonte` | enum | `ativo`, `manual`, `futuro`, `quarentena` ou `bloqueado`. |
| `ingestion_method` | enum | `manual_json`, `manual_csv`, `notebooklm`, `scraper_html`, `pdf`, `api`. |
| `source_snapshot_path` | string/null | Caminho local do snapshot, se houver. |
| `raw_payload_hash` | string/null | Hash do HTML/PDF/CSV bruto, se houver. |

Regra: pelo menos um entre `source_snapshot_path` e `raw_payload_hash` deve
existir para o lote ser candidato a importacao. Sem isso, o lote pode ser
analisado, mas fica em quarentena.

## Tipos de registro aceitos no v0

| `record_type` | Uso | Pode alimentar |
|---|---|---|
| `standings` | Classificacao por time | catalogo, times, radar |
| `fixture` | Jogo agendado | calendario, catalogo |
| `result` | Placar encerrado | motor, backtest, radar |
| `discipline_team` | CA/CV agregado por time | radar disciplinar |
| `news` | Noticia com URL original | contexto, UI |
| `odds` | Odds manuais com casa/mercado/timestamp | banca futura |
| `absence` | Lesao/suspensao/desfalque manual | contexto, alerta |

## Campos obrigatorios por registro

| Campo | Tipo | Regra |
|---|---|---|
| `record_id` | string | Id unico dentro do lote. |
| `record_type` | enum | Um dos tipos aceitos no v0. |
| `natural_key` | string | Chave natural para deduplicacao. |
| `status` | enum | `ok`, `quarentena`, `conflito` ou `rejeitado`. |
| `quality_score` | number | 0 a 5; pode herdar da fonte, mas deve vir explicito. |
| `evidence` | object | Trecho, linha, pagina ou seletor que justifica o dado. |
| `payload` | object | Dado extraido, com `null` para campos ausentes. |

## Evidencia minima

Cada registro deve ter ao menos uma evidencia:

| Campo | Quando usar |
|---|---|
| `page` | PDF ou documento paginado. |
| `line` | Texto extraido com linhas. |
| `selector` | HTML com seletor ou bloco identificavel. |
| `quote` | Trecho curto presente na fonte. |
| `table` | Nome ou indice da tabela. |

`quote` deve ser curto. Nao copiar artigos, paginas inteiras ou texto longo.

## CSV controlado

CSV e aceito como formato de transporte quando o operador ou ferramenta nao
conseguir gerar JSON confiavel.

Colunas obrigatorias:

```csv
schema_version,batch_id,record_id,record_type,natural_key,source_id,source_url,fetched_at,quality_score,status_fonte,ingestion_method,evidence_json,payload_json
```

Regras:

- `schema_version` deve ser `manual_source_batch_v0`.
- `evidence_json` deve ser JSON valido.
- `payload_json` deve ser JSON valido.
- Campos desconhecidos podem existir, mas o validador deve ignorar ou marcar
  como aviso. O dado importavel deve estar em `payload_json`.
- Linha sem `source_url` ou sem `fetched_at` nao vira fato.

## Payloads por tipo

### `standings`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 19,
  "position": 1,
  "team": "Palmeiras",
  "points": 41,
  "played": 18,
  "wins": 12,
  "draws": 5,
  "losses": 1,
  "goals_for": 30,
  "goals_against": 13,
  "goal_difference": 17,
  "yellow_cards": 40,
  "red_cards": 4,
  "points_percentage": 75
}
```

### `fixture`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 19,
  "match_date": "2026-07-18",
  "kickoff_time": "18:30",
  "timezone": "America/Sao_Paulo",
  "home_team": "Flamengo",
  "away_team": "Palmeiras",
  "stadium": null,
  "status": "scheduled"
}
```

### `result`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 18,
  "home_team": "Palmeiras",
  "away_team": "Santos FC",
  "home_goals": 2,
  "away_goals": 0,
  "status": "finished"
}
```

### `discipline_team`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 19,
  "team": "Palmeiras",
  "yellow_cards": 40,
  "red_cards": 4
}
```

### `news`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "team": "Palmeiras",
  "title": "Titulo da noticia na fonte",
  "url": "https://...",
  "published_at": null,
  "summary": null,
  "tags": ["palmeiras"]
}
```

Resumo gerado por ferramenta deve ficar marcado como resumo, nao como fato
numerico.

### `odds`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 19,
  "home_team": "Flamengo",
  "away_team": "Palmeiras",
  "bookmaker": "nome_da_casa",
  "market": "1x2",
  "selection": "home",
  "line": null,
  "odd": 2.1,
  "captured_at": "2026-06-15T12:00:00-03:00"
}
```

Odds sem casa, mercado e timestamp ficam em quarentena.

### `absence`

Campos esperados:

```json
{
  "competition": "brasileirao_serie_a",
  "season": 2026,
  "round": 19,
  "team": "Palmeiras",
  "player": "Nome do jogador",
  "reason": "suspenso",
  "status": "out",
  "valid_until": null
}
```

`absence` manual sem fonte primaria ou noticia identificavel nao deve ajustar
probabilidade. Pode aparecer apenas como pendencia/quarentena.

## Regras de rejeicao imediata

O lote ou registro deve ser rejeitado quando:

- nao tiver `source_url`;
- nao tiver `fetched_at`;
- usar texto como "provavelmente", "estima-se" ou "com base no conhecimento"
  dentro de campo factual;
- preencher campo ausente com valor inferido;
- tiver placar fora do limite de sanidade 0 a 20;
- tiver pontos, jogos, gols, CA ou CV negativos;
- tiver odd menor ou igual a 1.0;
- conflitar com dado oficial ja validado sem marcar `conflito`.

## Relacao com o banco

Este template nao escreve no banco. Ele prepara o lote para:

1. validacao local;
2. relatorio de divergencias;
3. aprovacao humana;
4. staging/quarentena;
5. importacao idempotente futura.

