# Mapa do `web/` — consumo de API e superfície de contrato

> **Fase 0 / branch `claude/web-map`.** Levantamento read-only do frontend atual.
> Objetivo: dar ao contract v0 (`engine → api → web`) a lista exata do que o web
> **já consome** hoje, para que o contrato seja **retrocompatível** e não quebre `/consulta`.
> Não altera nenhum contrato. Insumo para revisão, não o contrato em si.

## Stack
- Next.js 15 (App Router) · React 19 · Tailwind 3 · `@supabase/supabase-js`.
- **Sem** lib de charting, **sem** state manager, **sem** lib de componentes.
- Tokens de tema custom (Tailwind): `fz-green`, `fz-card`.
- Base da API: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- Auth: Supabase Auth no browser; token vai como `Authorization: Bearer` (`lib/api.ts`).

## Páginas (`app/`)
| Rota | Arquivo | Papel | Auth gate |
|------|---------|-------|-----------|
| `/` | `page.tsx` | Painel: 3 cards (notícias, próximos A, próximos B) | sim (redirect /login) |
| `/login` | `login/page.tsx` | login/cadastro Supabase | — |
| `/calendario` | `calendario/page.tsx` | semana/mês, filtro liga, navega p/ consulta | sim |
| `/consulta/[matchId]` | `consulta/[matchId]/page.tsx` | **tela de previsão — onde o radar vai morar** | **não** |
| `/historico` | `historico/page.tsx` | tabela de consultas passadas | **não** |
| `/noticias` | `noticias/page.tsx` | lista notícias ge.globo | sim |

Componente único: `components/Nav.tsx` (header + saldo de créditos + logout).
Libs: `lib/api.ts` (`apiGet`/`apiPost` + Bearer), `lib/supabase.ts` (client browser).

## Pontos de consumo de API (web → `api/`)
| Método | Endpoint | Resposta esperada | Quem usa |
|--------|----------|-------------------|----------|
| GET | `/catalog/matches` | `{ partidas: Match[] }` | calendario |
| GET | `/catalog/matches?status=agendado` | `{ partidas: Match[] }` | painel |
| GET | `/catalog/matches/{id}` | `{ partida: Partida }` | consulta |
| GET | `/catalog/news?limit=N` | `{ noticias: Noticia[] }` | painel, noticias |
| POST | `/queries` body `{ match_id, complexidade }` | `{ resultado: Resultado }` | consulta |
| GET | `/queries` | `{ consultas: Consulta[] }` | historico |
| GET | `/credits` | `{ saldo: number }` | Nav |
| (auth) | Supabase `signInWithPassword` / `signUp` | — | login |

## Shapes que o web já lê (= superfície do contrato a congelar)
```ts
TeamRef   = { nome: string; escudo_url?: string|null }   // consulta usa só {nome}
Match     = { id, liga, data_hora|null, rodada|null, status,
              placar_casa?|null, placar_fora?|null, mandante: TeamRef|null, visitante: TeamRef|null }
Partida   = { data_hora, rodada|null, status, local?, mandante: TeamRef|null, visitante: TeamRef|null }
Noticia   = { titulo, url, fonte, liga?|null, imagem_url?|null, publicado_em?|null }
Consulta  = { id, match_id, complexidade, custo_creditos, mercados: string[], status, created_at }

Resultado = {
  partida?: { mandante: string; visitante: string }
  baseline?: boolean
  forca_comparativa?: {
    mandante: { ifc: number; leitura: string }
    visitante: { ifc: number; leitura: string }
    diferenca_ifc: number
    expectativa_mandante: number
    leitura: string
    adversarios_comuns: { adversario, resultado_mandante, resultado_visitante }[]
    jogos_no_grafo: number
  } | null
  agregador?: {
    resultado: { prob_casa, prob_empate, prob_visitante, resultado_mais_provavel, placar_provavel }
    gols: { over_15, over_25, over_35, btts }
    escanteios: { over_85, over_95, over_105 }
  }
  trace?: { camada, topico, status, resumo?, justificativa?, fonte?, entrada, saida }[]
}
```

## Onde o radar vai morar
`/consulta/[matchId]`. Seções renderizadas quando `resultado.agregador` existe:
força comparativa (barras IFC + adversários comuns) · resultado provável (3 barras 1X2) ·
gols (grid 4) · escanteios (grid 3) · aviso `baseline` · accordion "como esta análise foi feita"
(trace por camada, status `ok`/`baseline`/`pendente`). O trace já é um pré-radar textual.

## Implicações diretas para o contract v0
1. **Não é greenfield.** O `Resultado.agregador` acima já é lido em produção — o contract v0
   **tem que ser retrocompatível** com esses campos, senão `/consulta` quebra.
2. **Folga existente:** o `engine/run.py` já retorna `indice_confianca`, `alertas`, `banca`,
   que o web **ignora hoje**. O contrato pode formalizá-los e o web passa a renderizar
   (confiança/alertas/banca) **sem breaking change**.
3. **Falta no shape, exigido pelo plano:** campo de **modo do agregador**
   (`nucleo_only` / `modelo_only` / `fallback_pesos`) para a UI mostrar "motor parcial".
   Hoje só existe o bool `baseline`.

## Gaps de UI para Fase 2+
- Sem componente de radar e sem chart lib → SVG na mão ou nova dependência (decisão de produto).
- Estados não padronizados: cada página rola seu próprio loading/empty/erro; auth gate
  duplicado e **inconsistente** (`/consulta` e `/historico` não redirecionam). Alvo do trabalho
  "dado ausente / camada pendente / motor parcial".
- Nenhuma renderização de confiança/alertas/banca apesar de o motor já enviar.
