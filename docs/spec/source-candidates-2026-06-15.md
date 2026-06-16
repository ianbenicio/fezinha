# Fontes candidatas informadas pelo usuario - 2026-06-15

Status: candidatas nao aprovadas
Autor do registro: Codex
Origem: lista fornecida pelo usuario

## Regra de uso

Estas fontes ainda nao estao aprovadas para popular banco, motor, agregador ou
banca. Elas entram como backlog de ingestao e pesquisa.

Antes de qualquer automacao:

- verificar URL oficial e termos de uso;
- confirmar cobertura para Brasileirao Serie A/B 2026;
- definir campos exatos a extrair;
- guardar `source_url`, `fetched_at`, snapshot/hash e qualidade;
- passar por validador/staging;
- decidir uso permitido por modulo;
- nunca completar dado ausente por LLM.

## Dados estruturais - mensal

| Fonte | URL inicial | Dados candidatos | Status inicial | Uso permitido agora |
|---|---|---|---|---|
| Transfermarkt BR | `https://www.transfermarkt.com.br/` | elenco completo, valores de mercado, transferencias | `futuro` | pesquisa/manual, sem motor |
| oGol | `https://www.ogol.com.br/` | historico de confrontos, fichas, resultados historicos | `futuro` | pesquisa/manual, backtest futuro |
| FootStats | `https://www.footstats.com.br/` | historico e estatisticas, se cobertura/licenca forem confirmadas | `futuro` | pesquisa/manual |

Observacao:

- valor de mercado e dado estrutural, nao deve entrar direto como probabilidade;
- pode virar variavel exploratoria apos backtest;
- elenco do Transfermarkt nao substitui escalacao confirmada.

## Dados de performance - por jogo

| Fonte | URL inicial | Dados candidatos | Status inicial | Uso permitido agora |
|---|---|---|---|---|
| FBref | `https://fbref.com/` | xG, xGA, passes, progressivos, PPDA se disponivel | `futuro` | pesquisa; scraper exige cuidado |
| SofaScore | `https://www.sofascore.com/` | finalizacoes, posse, desarmes, interceptacoes, escanteios, cartoes/faltas | `futuro` | pesquisa/manual |
| WhoScored | `https://www.whoscored.com/` | posse, ratings, estatisticas de jogo | `futuro` | pesquisa/manual |

Observacao:

- xG/PPDA precisam de confirmacao de cobertura por Brasileirao e por temporada;
- estatisticas por jogo podem alimentar radar/motor futuro, mas exigem
  normalizacao por time, mando, liga e amostra;
- se o site bloquear coleta automatica, nao contornar bloqueio.

## Dados contextuais - semanal/pre-jogo

| Fonte | URL inicial | Dados candidatos | Status inicial | Uso permitido agora |
|---|---|---|---|---|
| ge.globo | `https://ge.globo.com/futebol/brasileirao-serie-a/` | lesoes, suspensoes, provaveis escalacoes, mudanca de tecnico, bastidores | `manual` | contexto/UI com fonte |
| CBF | `https://www.cbf.com.br/` | suspensoes e documentos oficiais quando disponiveis | `ativo/manual` | fato oficial apos parser/validacao |
| ESPN Brasil | `https://www.espn.com.br/futebol/` | noticias, analise e contexto | `manual` | contexto/editorial |
| UOL Esporte | `https://www.uol.com.br/esporte/futebol/` | noticias, analise e contexto | `manual` | contexto/editorial |
| Footure | `https://footure.com.br/` | analise tatica/contextual | `quarentena` | pesquisa/hipotese |

Observacao:

- noticia pode explicar contexto, mas nao vira numero sem regra;
- provavel escalacao nao e escalacao confirmada;
- bastidor precisa ficar como alerta/contexto, nao fato numerico;
- Footure e analitico/editorial: util para pesquisa, nao para motor sem teste.

## Dados de mercado - pre-jogo

| Fonte | URL inicial | Dados candidatos | Status inicial | Uso permitido agora |
|---|---|---|---|---|
| The Odds API | `https://the-odds-api.com/` | odds automatizadas, mercados h2h/over-under, bookmakers | `futuro` | API candidata |
| OddsPortal | `https://www.oddsportal.com/` | odds 1x2, over/under, BTTS, movimento de odds | `futuro` | pesquisa/manual |
| Bet365 | `https://www.bet365.com/` | odds de escanteios/cartoes e mercados especificos | `manual` | entrada manual validada |

Observacao:

- odds so entram em banca quando houver odds validas e probabilidade calibrada;
- no fallback atual, odds podem participar da fusao explicativa, mas
  `banca.recomendacoes` continua vazia;
- movimento de odds precisa de timestamp e coleta antes do jogo;
- OddsPortal e Bet365 exigem revisao forte de termos antes de automacao.

## Priorizacao tecnica

1. The Odds API: melhor candidata para automacao de odds, se cobrir Brasil e
   mercados necessarios.
2. ge.globo + CBF: melhor fonte inicial para contexto verificavel e suspensoes.
3. SofaScore/FBref: performance por jogo, mas so depois de validar cobertura e
   termos.
4. Transfermarkt: estrutural mensal, util para elenco/valor, nao para decisao
   imediata.
5. ESPN/UOL/Footure: contexto editorial, sempre separado do motor numerico.
6. OddsPortal/Bet365: podem ser usados manualmente; automacao depende de termos.

## Evidencias rapidas verificadas nesta sessao

- The Odds API expoe planos, API key, bookmakers, Campeonato Brasileiro Serie A
  e mercados como head-to-head e totals.
- SofaScore declara cobertura de Brasileirao Serie A, estatisticas, tabelas,
  fixtures, cartoes, substituicoes e odds em detalhes de partida.
- Transfermarkt se apresenta como portal de transferencias, valores de mercado,
  rumores e estatisticas.
- OddsPortal se apresenta como comparador de odds, mercados pre-match/in-play,
  dropping odds, resultados e standings.

## Pendencias

- Revisar termos/licenca de cada fonte.
- Confirmar cobertura exata Serie A/B 2026.
- Definir se cada fonte sera parser, API, manual batch ou apenas pesquisa.
- Criar amostra pequena e validar contra `manual_source_batch_v0`.
- Decidir quais dados merecem banco e quais ficam apenas como link/contexto.
