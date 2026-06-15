# Catalogo de Fontes v0

Status: proposto
Versao: v0
Data: 2026-06-15
Escopo: criterios para avaliar sites/fontes e decidir como cada dado entra no Fezinha

## 1. Objetivo

Este documento define como o Fezinha deve catalogar fontes externas antes de
usar seus dados em banco, motor, radar, telas ou backtests.

A regra central e:

```text
Dado factual vem de fonte verificavel. Sem fonte, sem linha factual.
```

LLM ou operador humano podem classificar, resumir ou apontar candidatos, mas
nao sao fonte primaria de placar, data, time, odds, cartao, lesao, escalacao,
xG ou qualquer valor numerico.

## 2. Resultado esperado do catalogo

Cada site/fonte analisado deve virar um registro com:

```yaml
id: cbf_tabelas
nome: CBF - Tabelas
url_base: https://www.cbf.com.br/
tipo_fonte: oficial_primaria
status_operacional: ativo | manual | futuro | quarentena | bloqueado
dados_cobertos: [jogos, resultados, classificacao, ca_cv]
custo: gratis | pago | manual | desconhecido
licenca_uso: permitido | revisar_tos | nao_permitido | desconhecido
confiabilidade: 0..5
automacao: direta | scraper_html | pdf | manual | api
frequencia_recomendada: diario | por_rodada | pre_jogo | pos_jogo | sob_demanda
proveniencia_obrigatoria: true
snapshot_obrigatorio: true
uso_permitido: [catalogo, radar, motor, backtest, noticia, alerta]
uso_proibido: [odds, escalacao]
observacoes: ""
```

## 3. Tipos de fonte

| Tipo | Descricao | Pode alimentar | Risco |
|---|---|---|---|
| `oficial_primaria` | Entidade dona da competicao ou do clube | fatos, calendario, resultados, classificacao | HTML/PDF pode mudar |
| `api_licenciada` | API com termos claros e dado estruturado | stats, jogador, lesao, escalacao, odds se licenciado | custo, limite, cobertura |
| `midia_confiavel` | Veiculo jornalistico com historico e autoria | noticias, contexto, fatos relevantes | texto pode ser interpretativo |
| `clube_oficial` | Site/rede oficial do clube | nota oficial, lista de relacionados, coletiva | vies institucional |
| `mercado_odds` | Casa/API de odds | odds, linha, movimento de mercado | licenca, latencia, margem |
| `meteorologia` | API meteorologica documentada | clima, temperatura, chuva, vento | precisa local/coordenada |
| `manual_operador` | Entrada humana controlada | odds manuais, desfalques, ajustes temporarios | erro humano |
| `social_ou_rumor` | rede social, forum, rumor, influencer | somente hipotese/quarentena | falso positivo alto |

## 4. Tipos de dado

| Tipo de dado | Exemplos | Exigencia minima para banco | Uso inicial |
|---|---|---|---|
| `identidade_time` | id, nome, escudo, liga | fonte oficial ou catalogo normalizado | catalogo, times |
| `calendario` | rodada, data, estadio, mandante, visitante | fonte oficial ou ge com snapshot | catalogo |
| `resultado` | placar, status encerrado | fonte oficial, snapshot e hora de coleta | motor, backtest |
| `classificacao` | PTS, J, V, E, D, GP, GC, SG, aproveitamento | fonte oficial/ge com snapshot | times, radar |
| `disciplina_agregada` | CA, CV por time | CBF ou API com snapshot | radar, futura camada disciplina |
| `estatistica_time` | finalizacoes, posse, xG, PPDA | API licenciada ou fonte validada | radar futuro, motor futuro |
| `estatistica_jogador` | minutos, xG+xA, cartoes, status | API licenciada ou entrada manual validada | elenco futuro |
| `lesao_suspensao` | jogador fora, duvida, suspenso | fonte oficial/API/noticia com validade | modificador, alerta |
| `escalacao` | titular, reserva, relacionado | fonte oficial/API, timestamp pre-jogo | elenco, modificador |
| `noticia` | titulo, URL, resumo, tags | URL, fonte, publicado_em | contexto, UI |
| `odds` | casa, mercado, linha, odd, timestamp | origem, hora, mercado, casa | banca, agregador |
| `clima` | chuva, vento, temperatura | API meteo + coordenada estadio | clima futuro |

## 5. Escala de confiabilidade

| Nota | Definicao | Uso permitido |
|---:|---|---|
| 0 | ausente, ilegivel, sem fonte ou bloqueado | nao usar |
| 1 | rumor, social, texto sem verificacao independente | quarentena/hipotese |
| 2 | fonte secundaria ou manual sem dupla checagem | UI com aviso, nunca motor numerico |
| 3 | fonte confiavel, mas scraper fragil ou cobertura parcial | catalogo/UI/radar com qualidade |
| 4 | oficial ou API estruturada, com snapshot e validacao | banco, radar, backtest |
| 5 | oficial/API estruturada, historico completo, schema estavel e validacao cruzada | motor, agregador, banca quando aplicavel |

Regra: dado com confiabilidade menor que 4 nao deve alterar probabilidade,
EV, stake ou recomendacao de aposta.

## 6. Status operacional

| Status | Significado |
|---|---|
| `ativo` | fonte ja pode ser coletada com processo definido |
| `manual` | pode ser usada por entrada humana validada |
| `futuro` | boa fonte, mas falta acesso, custo ou desenvolvimento |
| `quarentena` | pode ser monitorada, mas nao entra como fato |
| `bloqueado` | nao usar por termos, baixa qualidade ou risco tecnico |

## 7. Politica de entrada no banco

### 7.1 Campos obrigatorios por registro factual

Todo registro factual inserido por ingestao deve guardar, direta ou
indiretamente:

```text
source_id
source_url
source_snapshot_path ou raw_payload_hash
fetched_at
published_at, quando existir
quality_score
status_fonte
ingestion_method
```

Se a tabela atual ainda nao tiver essas colunas, a ingestao deve manter o
payload bruto ou registrar a fonte em tabela auxiliar antes de automatizar em
producao.

### 7.2 O que entra no banco

Entra:

- dado factual verificavel;
- dado manual com fonte anexada;
- noticia com URL original;
- odds com casa, mercado, linha e timestamp;
- modificador com fonte, validade e responsavel/metodo de classificacao.

Nao entra como fato:

- texto gerado por LLM sem URL/fonte;
- rumor sem fonte;
- dado "completado" por suposicao;
- resultado inferido por memoria;
- escalacao provavel sem fonte e timestamp.

### 7.3 Conflitos entre fontes

Quando duas fontes divergem:

1. fonte oficial vence fonte secundaria;
2. se duas oficiais divergem, nao sobrescrever silenciosamente;
3. gravar conflito em status `conflito`;
4. manter ultimo valor validado;
5. exigir revisao manual antes de atualizar dado sensivel.

Dado sensivel inclui resultado, data/hora, time, odds, escalacao e lesao.

## 8. Uso permitido por modulo

| Modulo | Fontes permitidas | Observacao |
|---|---|---|
| `catalogo` | oficial_primaria, midia_confiavel validada | identidade, jogos, tabela |
| `radar` | oficial_primaria, api_licenciada, manual validado | exploratorio, nao altera probabilidade |
| `motor_estatistico` | oficial_primaria, api_licenciada nota >= 4 | sem texto interpretativo |
| `contextual` | midia_confiavel, clube_oficial, manual validado | gera leitura/modificador, com fonte |
| `odds_banca` | mercado_odds, manual_operador validado | sem odds, sem EV/stake |
| `backtest` | resultado oficial e previsao registrada antes do jogo | sem dado do futuro |
| `noticias_ui` | midia_confiavel, clube_oficial | filtro aproximado deve ser rotulado |

## 9. Lista inicial de fontes candidatas

| Fonte | Tipo | Dados candidatos | Status inicial | Uso recomendado |
|---|---|---|---|---|
| CBF Tabelas | oficial_primaria | jogos, resultados, classificacao, CA/CV, artilharia | `ativo` | base factual, radar, backtest |
| CBF PDFs | oficial_primaria | tabela detalhada, datas, jogos | `manual` | validacao e snapshot |
| ge.globo | midia_confiavel | noticias, escudos, calendario, forma exibida | `ativo` | catalogo, noticias, UI |
| API-Football | api_licenciada | lesoes, escalacao, stats de jogo/jogador, xG se disponivel | `futuro` | elenco, xG, disciplina avancada |
| Open-Meteo | meteorologia | clima por coordenada e data | `futuro` | camada clima |
| Odds manuais | manual_operador | odds por casa/mercado | `manual` | banca futura, sem automacao inicial |
| Sites de palpite | midia_confiavel ou social_ou_rumor | palpites/editorial | `quarentena` | nao usar no agregador ate prova |
| Redes sociais | social_ou_rumor | rumores, sinal antecipado | `quarentena` | nunca fato sem confirmacao |

## 10. Relacao com o radar de times

Os eixos do radar MVP devem ser amarrados a fontes permitidas:

| Eixo | Fonte MVP | Status esperado inicial |
|---|---|---|
| `forca_ofensiva` | CBF resultados/classificacao | `ok` se jogos suficientes |
| `solidez_defensiva` | CBF resultados/classificacao | `ok` se jogos suficientes |
| `forma_recente` | CBF/ge jogos recentes | `ok` se jogos suficientes |
| `consistencia` | CBF resultados recentes | `ok` ou `baixa_amostra` |
| `contexto_casa_fora` | CBF resultados com mando | `ok` ou `baixa_amostra` |
| `controle_disciplinar` | CBF CA/CV agregado; API-Football para detalhe futuro | `dado_ausente` ate ingestao CA/CV |

Enquanto CA/CV nao for ingerido, o eixo disciplinar fica presente no contrato,
mas com:

```json
{
  "status": "dado_ausente",
  "qualidade": 0,
  "base": null,
  "atual": null,
  "motivo_ausencia": "CA/CV ainda nao ingeridos da fonte oficial"
}
```

## 11. Promocao de fonte

Uma fonte so passa de `quarentena` ou `futuro` para `ativo` quando:

- tiver URL/base documentada;
- o dado extraido for reproduzivel;
- houver snapshot ou hash do payload;
- houver regra de normalizacao;
- houver teste ou amostra manual validada;
- o uso permitido estiver definido;
- o risco de termos/licenca estiver aceito pelo humano responsavel.

## 12. Proximos passos

O detalhamento operacional destas tarefas esta em:

```text
docs/coordination/source-ingestion-flow-tasks.md
```

Sequencia resumida:

1. Criar uma lista operacional de fontes em formato YAML/JSON baseada neste
   documento. Feito em `docs/spec/source-registry-v0.yaml`.
2. Adicionar CBF Tabelas como primeira fonte formal. Feito em
   `docs/spec/source-registry-v0.yaml`.
3. Definir parser de classificacao CBF com CA/CV agregado e jogos/resultados.
   Implementado em `engine/ingestion/cbf_tabelas.py`.
4. Amarrar `radar_time` a este catalogo.
5. So depois automatizar novas fontes.

