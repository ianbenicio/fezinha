# Ingestão de Dados (`engine/ingestion/`)

Coleta dados externos que alimentam as camadas. Fonte principal: **API-Football**
(api-sports.io) — uma API legal cobre ~9 camadas. FBref foi descartado: bloqueia
IP de datacenter (403), inviável no servidor.

## Mapa: camada → dado → formato → fonte

| Camada / módulo | Dado que consome | Tabela destino | Fonte |
|---|---|---|---|
| `pi_ratings`, `forca_comparativa`, `h2h`, `perfil_liga` | resultados (placar, mando, data) | `matches` | API-Football `/fixtures` · CBF (PDF) |
| `dixon_coles` | xG por time/jogo | `match_stats.xg` | API-Football `/fixtures/statistics` |
| `tatica_matchup` | posse, finalizações, escanteios | `match_stats` | idem |
| `pi_ratings` (escanteios) | escanteios por time | `match_stats.escanteios` | idem |
| `elenco_impacto` (A EDGE) | xG+xA/min, minutos, jogos por jogador | `player_stats` | API-Football `/players` |
| `elenco_impacto` | lesão/suspensão/dúvida, cartões pendurados | `player_status` | API-Football `/injuries` |
| `arbitragem` | árbitro do jogo (+ perfil) | `matches.arbitro` | API-Football `/fixtures` |
| `clima` | chuva/vento/temp @ estádio | `weather` (futuro) | OpenWeather (API) |
| `odds`, `movimento_mercado` | odds 1x2/over por casa, abertura+atual | `odds_snapshots` (futuro) | the-odds-api |
| `fatos_relevantes`, `visao_time` | notícias/declarações | `news` (futuro) | portais → LLM extrai |
| `consenso_externo` | palpites de sites | `external_picks` (futuro) | Forebet/PredictZ |
| `contexto_competitivo` | tabela de classificação | derivado de `matches` | — (calculado) |

## Formato dos dados (tabelas)

- **`match_stats`** (1 linha por time por jogo): `xg`, `posse` (int %), `escanteios`,
  `finalizacoes`, `finalizacoes_no_gol`, `faltas`, `cartoes_amarelos/vermelhos`.
- **`player_stats`** (1 por jogador/temporada): `jogos`, `minutos`, `gols`,
  `assistencias`, `xg`, `xa`, `cartoes_*`.
- **`player_status`**: `status` (ativo/lesionado/suspenso/duvida), `motivo`,
  `cartoes_pendurados`.
- Mapeamento idempotente via `teams.api_team_id`, `players.api_player_id`,
  `matches.api_fixture_id`.

## Como rodar (`api_football.py`)

1. Crie conta grátis em **dashboard.api-football.com** → copie a API key.
2. No `.env`: `API_FOOTBALL_KEY=...` (+ `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`).
3. Na ordem (free tier = 100 req/dia):

```bash
python -m engine.ingestion.api_football teams      # 1x — mapeia api_team_id
python -m engine.ingestion.api_football fixtures   # jogos + resultados + árbitro
python -m engine.ingestion.api_football stats      # xG/posse/escanteios (lotes de 15)
python -m engine.ingestion.api_football players    # jogadores + xG+xA/min
python -m engine.ingestion.api_football injuries   # lesões/suspensões
```

- **`teams` primeiro** (os outros dependem do mapa `api_team_id`).
- `stats` processa 15 jogos por execução (cota); rode em dias seguidos até cobrir tudo.
- Idempotente: re-rodar atualiza, não duplica.

## Agendamento (produção)

Cron — GitHub Actions (grátis) ou worker Railway:
- `fixtures` + `injuries`: diário (resultados e lesões mudam)
- `stats`: após cada rodada
- `players`: semanal

## Legalidade

API oficial com key (uso permitido pelo tier). Sem scraping de sites que bloqueiam.
Notícias (futuro): extrair fato + linkar fonte, nunca copiar texto.
