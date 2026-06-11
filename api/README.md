# Fezinha API (backend)

FastAPI + Supabase. Auth, créditos, consultas, catálogo.

## Setup

```bash
cd fezinha
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r api/requirements.txt
cp .env.example .env          # preencher SUPABASE_* e ANTHROPIC_API_KEY
```

`.env` precisa de:
- `SUPABASE_URL` — https://thrkaovwrtlqreutxsjp.supabase.co
- `SUPABASE_PUBLISHABLE_KEY` — pública (frontend)
- `SUPABASE_SERVICE_ROLE_KEY` — **secreta**, painel → Settings → API → service_role

## Rodar

```bash
uvicorn api.main:app --reload
```

- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health

## Rotas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/me` | perfil + saldo |
| PATCH | `/me` | atualiza perfil_risco / preferências |
| GET | `/credits` | saldo |
| GET | `/credits/transactions` | histórico de transações |
| POST | `/queries` | nova consulta (debita crédito, roda motor) |
| GET | `/queries` | histórico de consultas |
| GET | `/queries/{id}` | detalhe da consulta |
| GET | `/catalog/teams` | times da liga |
| GET | `/catalog/teams/{id}` | time + jogadores |
| GET | `/catalog/matches` | partidas |

Todas (exceto `/health`) exigem `Authorization: Bearer <supabase_access_token>`.

## Custo por consulta (configurável em `pricing.py`)

| Complexidade | Créditos | Mercados | Camadas LLM |
|--------------|----------|----------|-------------|
| simples | 1 | 1X2 | — |
| padrao | 3 | todos | 3 |
| premium | 5 | todos | 6 |

## Notas

- **Motor é stub** (`engine_stub.py`) — retorna estrutura do agregador com zeros até as camadas (`../layers/`) virarem código Python em `../engine/`. Interface estável.
- **Auth MVP** — `core.py` decodifica o JWT sem verificar assinatura. Antes de produção: validar via JWKS do Supabase.
- Débito/estorno de crédito são **atômicos** (funções SQL `consumir_creditos` / `estornar_creditos`, com lock de linha).
