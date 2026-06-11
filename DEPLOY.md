# Deploy do Fezinha

Backend → **Railway** · Frontend → **Vercel** · Banco → **Supabase** (já no ar).

Ordem: 1) backend Railway → 2) frontend Vercel → 3) ajustar CORS → 4) Supabase auth.

---

## 1. Backend (Railway)

1. https://railway.app → **New Project** → **Deploy from GitHub repo** → `ianbenicio/fezinha`
2. Railway detecta Python (requirements.txt na raiz) e usa o `Procfile`:
   `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
3. **Variables** (Settings → Variables):

   | Variável | Valor |
   |----------|-------|
   | `SUPABASE_URL` | `https://thrkaovwrtlqreutxsjp.supabase.co` |
   | `SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_2F5EYobrexvZqV1q-cPuNg_c_K_K-tH` |
   | `SUPABASE_SERVICE_ROLE_KEY` | *(painel Supabase → Settings → API → service_role — SECRETO)* |
   | `ALLOWED_ORIGINS` | *(preencher no passo 3 com o domínio Vercel)* |

4. Deploy → Railway gera uma URL pública, ex: `https://fezinha-production.up.railway.app`
   → **anote essa URL** (vai no frontend).
5. Teste: abrir `https://<railway-url>/health` → deve responder `{"status":"ok"}`.

---

## 2. Frontend (Vercel)

1. https://vercel.com → **Add New Project** → import `ianbenicio/fezinha`
2. **Root Directory** → `web`  (monorepo — importante!)
3. Framework: Next.js (autodetectado)
4. **Environment Variables**:

   | Variável | Valor |
   |----------|-------|
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://thrkaovwrtlqreutxsjp.supabase.co` |
   | `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_2F5EYobrexvZqV1q-cPuNg_c_K_K-tH` |
   | `NEXT_PUBLIC_API_URL` | a URL do Railway (passo 1.4) |

5. Deploy → Vercel gera o link, ex: `https://fezinha.vercel.app` → **esse é o link de teste**.

---

## 3. Liberar CORS (volta no Railway)

No Railway, setar `ALLOWED_ORIGINS` com o domínio Vercel:

```
ALLOWED_ORIGINS=https://fezinha.vercel.app
```

Railway redeploya. Sem isso, o navegador bloqueia as chamadas do front ao back.

---

## 4. Supabase Auth (teste rápido)

Por padrão o cadastro exige confirmar e-mail. Para testar sem isso:

- Painel Supabase → **Authentication → Providers → Email** → desligar
  *"Confirm email"* (só para teste; religar antes de público).

Ou: cadastre e confirme o e-mail normalmente.

---

## ⚠️ Antes de divulgar publicamente

- **Hardening JWT** — `api/core.py` ainda não valida a assinatura do token
  (decodifica sem verificar). Para uso fechado/teste é aceitável; para público,
  validar via JWKS do Supabase primeiro.
- Religar confirmação de e-mail.
- Revisar rate limiting / limites de crédito.

---

## Resumo das URLs (preencher após deploy)

```
Frontend:  https://__________.vercel.app   ← link de teste
Backend:   https://__________.up.railway.app
Banco:     https://thrkaovwrtlqreutxsjp.supabase.co
```
