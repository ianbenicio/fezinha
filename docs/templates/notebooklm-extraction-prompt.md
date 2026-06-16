# Prompt de extracao - NotebookLM / ferramenta equivalente

Status: ativo para bootstrap manual
Versao: v0
Data: 2026-06-15
Saida alvo: `manual_source_batch_v0`

## Como usar

Cole este prompt na ferramenta junto com a fonte original ou com o documento
extraido da fonte. Ajuste apenas os campos entre colchetes.

O objetivo e extrair dados presentes na fonte, nao interpretar nem completar.

## Prompt

```text
Voce vai extrair dados para o projeto Fezinha usando o formato
manual_source_batch_v0.

REGRA PRINCIPAL
- Extraia somente valores que estejam explicitamente presentes na fonte
  fornecida nesta conversa.
- Nao use memoria, conhecimento previo, internet externa, inferencia,
  estimativa, probabilidade, opiniao ou completamento automatico.
- Se um campo nao estiver explicitamente na fonte, use null.
- Se houver duvida, marque o registro como "quarentena" e explique em notes.
- Nao corrija nomes de times por conta propria. Preserve o nome como aparece
  na fonte.
- Nao deduza placar, data, rodada, CA, CV, odds, lesao, escalacao ou xG.
- Nao misture dados de fontes diferentes no mesmo registro sem indicar isso.

FONTE
- source_id: [ex: cbf_tabelas]
- source_name: [ex: CBF - Tabelas]
- source_url: [cole a URL original da fonte, nao a URL do NotebookLM]
- source_type: [oficial_primaria | api_licenciada | midia_confiavel |
  clube_oficial | mercado_odds | meteorologia | manual_operador |
  social_ou_rumor]
- fetched_at: [AAAA-MM-DDTHH:MM:SS-03:00]
- source_snapshot_path: [caminho local do HTML/PDF/CSV salvo, ou null]
- raw_payload_hash: [hash do arquivo bruto, ou null]
- quality_score: [0 a 5]
- status_fonte: [ativo | manual | futuro | quarentena | bloqueado]
- ingestion_method: notebooklm

DADOS A EXTRAIR
Extraia, se estiverem presentes na fonte:
1. classificacao por time (`standings`);
2. jogos agendados (`fixture`);
3. resultados encerrados (`result`);
4. cartoes agregados por time, CA e CV (`discipline_team`);
5. noticias com URL original (`news`);
6. odds somente se a fonte for casa/API/entrada manual com timestamp (`odds`);
7. desfalques, lesoes ou suspensoes somente quando a fonte citar claramente
   jogador, time, motivo e data/contexto (`absence`).

SAIDA
Responda apenas com JSON valido, sem Markdown, sem comentario fora do JSON.
Use exatamente esta estrutura:

{
  "schema_version": "manual_source_batch_v0",
  "batch_id": "[id curto e unico do lote]",
  "created_at": "[AAAA-MM-DDTHH:MM:SS-03:00]",
  "created_by": "notebooklm",
  "notes": null,
  "source": {
    "source_id": "[source_id]",
    "source_name": "[source_name]",
    "source_url": "[source_url]",
    "source_type": "[source_type]",
    "fetched_at": "[fetched_at]",
    "quality_score": [quality_score],
    "status_fonte": "[status_fonte]",
    "ingestion_method": "notebooklm",
    "source_snapshot_path": [string ou null],
    "raw_payload_hash": [string ou null],
    "extraction_tool": "NotebookLM"
  },
  "records": [
    {
      "record_id": "[id unico dentro do lote]",
      "record_type": "[standings | fixture | result | discipline_team | news | odds | absence]",
      "natural_key": "[chave natural deterministica]",
      "status": "[ok | quarentena | conflito | rejeitado]",
      "quality_score": [0 a 5],
      "evidence": {
        "page": [numero ou null],
        "line": [numero ou null],
        "selector": [string ou null],
        "quote": "[trecho curto da fonte ou null]",
        "table": [string ou null]
      },
      "payload": {
        "...": "campos conforme o tipo do registro"
      }
    }
  ]
}

REGRAS PARA NATURAL_KEY
- standings: competition:season:round:team:standings
- fixture: competition:season:round:home_team:away_team:fixture
- result: competition:season:round:home_team:away_team:result
- discipline_team: competition:season:round:team:discipline_team
- news: news:url_original
- odds: competition:season:round:home_team:away_team:odds:bookmaker:market:selection:captured_at
- absence: competition:season:round:team:player:absence

REGRAS DE STATUS
- Use "ok" apenas quando o valor estiver claro na fonte.
- Use "quarentena" quando houver fonte, mas a extracao for ambigua,
  incompleta ou textual.
- Use "conflito" quando a fonte mostrar valores divergentes para o mesmo dado.
- Use "rejeitado" quando a fonte nao permitir sustentar o dado.

REGRAS DE EVIDENCIA
- Cada registro precisa ter pelo menos um destes campos preenchido:
  page, line, selector, quote ou table.
- quote deve ser curto, apenas o trecho necessario para localizar o dado.
- Nao copie artigos, paginas inteiras ou texto longo.

REGRAS DE CAMPOS AUSENTES
- Campo ausente = null.
- Nao use zero para ausente.
- Nao use "-" para ausente.
- Nao substitua time ausente por time provavel.
- Nao substitua horario ausente por horario comum de rodada.
- Nao substitua odds ausente por media de mercado.

VALIDACOES ANTES DE RESPONDER
- Todo registro tem source_url herdavel do lote.
- Todo registro tem fetched_at herdavel do lote.
- Todo record_id e unico.
- Toda natural_key e unica dentro do lote.
- Placar esta entre 0 e 20.
- Pontos, jogos, gols, CA e CV nao sao negativos.
- Odds, quando existirem, sao maiores que 1.0.
- Se source_snapshot_path e raw_payload_hash forem ambos null, mantenha os
  registros em quarentena.
```

## Prompt curto para CSV

Use este quando a ferramenta nao conseguir gerar JSON.

```text
Extraia somente dados explicitamente presentes na fonte. Nao use memoria,
inferencia, estimativa ou completamento. Campo ausente deve ser null.

Responda apenas em CSV com estas colunas:
schema_version,batch_id,created_at,created_by,record_id,record_type,natural_key,record_status,record_quality_score,source_id,source_name,source_url,source_type,fetched_at,source_quality_score,status_fonte,ingestion_method,source_snapshot_path,raw_payload_hash,evidence_json,payload_json

schema_version deve ser manual_source_batch_v0.
record_quality_score e source_quality_score devem ser numeros de 0 a 5.
evidence_json e payload_json devem ser JSON valido em uma linha.
Nao escreva explicacoes fora do CSV.
```

## Checklist humano antes de enviar ao Codex

- A URL original da fonte foi preenchida.
- A data/hora de coleta foi preenchida.
- Ha snapshot local ou hash do arquivo bruto.
- Campos ausentes estao como `null`.
- A ferramenta nao completou placares, horarios, CA/CV, odds ou jogadores.
- Noticias e desfalques vieram com URL ou evidencia localizavel.
- Odds tem casa, mercado e timestamp.
