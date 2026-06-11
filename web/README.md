# Fezinha Web (frontend)

Next.js 15 (App Router) + TypeScript + Tailwind + Supabase Auth.

## Setup

```bash
cd web
npm install
cp .env.local.example .env.local   # preencher a publishable key
npm run dev
```

- App: http://localhost:3000
- Precisa do backend rodando em http://localhost:8000 (ver `../api/README.md`)

## `.env.local`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` — pública
- `NEXT_PUBLIC_API_URL` — URL do backend FastAPI

## Telas

| Rota | Tela |
|------|------|
| `/login` | login / cadastro (Supabase Auth) |
| `/` | dashboard — próximas partidas |
| `/consulta/[matchId]` | escolher complexidade e analisar (gasta crédito) |
| `/historico` | histórico de consultas |

## Fluxo de auth

Supabase Auth no browser → guarda sessão → `lib/api.ts` injeta o
`access_token` como `Bearer` nas chamadas ao backend FastAPI. O backend valida
o JWT e aplica as regras de crédito.

## Pendente
- Catálogo mostra "Time #id" até o seed da Série A popular nomes/escudos.
- Resultado da consulta é JSON cru (motor stub). Vira UI rica quando o motor real existir.
- Telas de agenda e feed de notícias (fase posterior).
