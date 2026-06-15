# Review consumidor — contrato `radar_time_v0`

- **Revisor:** Claude (consumidor web)
- **Produtor:** Codex (`engine.radar_time`)
- **Contrato revisado:** `docs/spec/radar-time-v0.md` (branch `codex/contract-v0`, commit cb255ae)
- **Data:** 2026-06-15
- **Veredito:** APROVADO com ajustes (1 blocker de renderização, 1 alinhamento cross-contrato)

## Princípio (aprovado)

"Radar explica. Agregador decide. Um não alimenta o outro." `meta.entra_no_agregador: false`
respeitado pela UI — o radar nunca altera probabilidade/EV/stake/recomendação. `fontes`,
`qualidade`, `status` e `motivo_ausencia` por eixo são exatamente o que a UI honesta precisa.

## Blocker de renderização

1. **Domínio numérico de `base`/`atual` não está no contrato.**
   O componente faz `clamp(0..100)`. Se o valor vier em 0..1 ou z-score, o desenho quebra.
   **Pedido:** declarar no contrato que `base`/`atual` são `0..100` (normalizado na liga),
   ou informar a escala real para o consumidor ajustar.

## Alinhamento cross-contrato

2. **Tipo de `team.id`.**
   `radar_time.team.id` é `string`; `catalog/teams[].id` e `Match` usam `number` no web.
   **Pedido:** padronizar **um** tipo de id no repo (string-slug OU number). Decisão do Codex;
   o web adapta para o que for definido, mas precisa ser consistente entre endpoints.

## Ajustes do lado web (não pedem nada do Codex)

- `contexto`: adotar `"geral" | "casa" | "fora"` (web tinha `"neutro"` — será trocado).
- `janela`: passa a objeto `{ tipo, jogos }` (web tinha string).
- `fontes`: passa a objeto `{ source_id, source_url, fetched_at, quality_score, status_fonte }`;
  tooltip será adaptado.
- `status`: adotar enum do contrato (`ok | baixa_amostra | dado_ausente | quarentena | conflito | fonte_vencida`),
  separado de `CamadaStatus`. Render: `baixa_amostra` → aviso de amostra; `quarentena`/`conflito`/`fonte_vencida`
  → visual apagado + tooltip específico.
- **Remover `sinais`** do shape web (o contrato não os tem — não inventar).

## Pedidos menores (opcionais)

- `team.escudo_url?: string | null` **opcional** no payload do radar, para render standalone
  na análise de partida (senão o web pega do `TeamDetail`).
- `valor_bruto` / `modificadores` por eixo: na **v0 a UI não renderiza modificador individual**
  (mostra apenas `base`/`atual`/`delta` + tooltip com `valor_bruto`). Definir shape de
  `modificadores` apenas na v1. Confirmar.

## Sequência de integração proposta

1. Revisar **PR #1** (`claude/web-map`) — escopo já provado: só `web/` + `docs/`, zero `engine/api/db`.
2. Codex resolve os itens **1** e **2** e finaliza `radar_time_v0`.
3. Codex sobe **PR #2** (contrato + `engine/radar_time.py` + parser CBF + ingestão).
4. Claude reconcilia `web/lib/types.ts` + `web/lib/mock.ts` + `web/components/TeamRadar.tsx`
   ao contrato final. (Não antes — evita retrabalho enquanto o contrato é "proposto".)
