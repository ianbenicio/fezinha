# Review consumidor — contrato `radar_time_v0`

- **Revisor:** Claude (consumidor web)
- **Produtor:** Codex (`engine.radar_time`)
- **Contrato revisado:** `docs/spec/radar-time-v0.md` (branch `codex/contract-v0`, commit cb255ae)
- **Data:** 2026-06-15
- **Veredito:** APROVADO com ajustes — **produtor verificado** (`engine/radar_time.py` + `engine/test_radar_time.py`, branch `codex/contract-v0`)

## Princípio (aprovado)

"Radar explica. Agregador decide. Um não alimenta o outro." `meta.entra_no_agregador: false`
respeitado pela UI — o radar nunca altera probabilidade/EV/stake/recomendação. `fontes`,
`qualidade`, `status` e `motivo_ausencia` por eixo são exatamente o que a UI honesta precisa.

## Verificação do produtor (`engine/radar_time.py`)

Payload emitido bate 1:1 com o contrato (`schema_version`, `team`, `referencia`, `contexto`,
`eixos[]`, `meta`). Asserts em `test_radar_time.py` confirmam `schema_version`,
`entra_no_agregador: false`, status por eixo e `janela.tipo`.

## Blocker de renderização — RESOLVIDO no código

1. ~~Domínio numérico de `base`/`atual` não está no contrato.~~
   **Resolvido:** `_scale_minmax()` retorna `round(max(0.0, min(100.0, score)), 2)` e todos os
   eixos escalam `×100`. Logo `base`/`atual` ∈ **[0, 100]** — o `clamp(0..100)` do componente
   está correto. **Pedido remanescente (doc):** declarar o range `0..100` no próprio
   `radar-time-v0.md` (hoje só está implícito no código).

## Alinhamento cross-contrato — ainda aberto

2. **`team.id` é slug derivado do NOME, não id de banco.**
   No engine, `team.id = _slug(nome)` (ex.: `"Atlético-MG"` → `"atletico-mg"`). Já o
   `catalog/teams[].id` e `Match` usam `number` no web, e a rota é `/times/[teamId]`.
   **Risco real:** o `teamId` da rota web não casa com o `team.id` do radar.
   **Pedido:** o `catalog/teams` precisa expor o mapeamento slug↔id (ou o web roteia por slug).
   Decisão do Codex; o web adapta para o que for definido, mas precisa ser consistente.

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

## Observações do produtor (menores, não bloqueiam)

- **`delta` é sempre 0 na v0:** todo eixo computa `base == atual` e `modificadores: []`.
  Os dois polígonos do radar (base tracejado vs atual sólido) **coincidem** na v0.
  Mantenho o desenho duplo (pronto para v1 com modificadores), mas é redundante por ora —
  alternativa: na v0 desenhar só `atual`. A decidir no reconcile.
- **Status emitido na v0 = 3 de 6:** só `ok | baixa_amostra | dado_ausente`.
  `quarentena | conflito | fonte_vencida` estão no enum mas ainda não são produzidos.
  Consumidor trata os 3 atuais; os outros 3 ficam prontos para quando o engine emitir.
- **`eixo.referencia` vem `{liga: null, temporada: null}` hardcoded** — a referência real
  está no `referencia` de topo. Campo por-eixo é vestigial; usar o de topo.
- **Disciplina acende** quando o lote traz `yellow_cards`/`red_cards` (record `discipline_team`
  ou na própria linha de `standings`); senão `dado_ausente` com motivo "CA/CV nao encontrados".
  Confirma o plano: eixo fica apagado até a ingestão de cartões da CBF.

## Sequência de integração proposta

1. Revisar **PR #1** (`claude/web-map`) — escopo já provado: só `web/` + `docs/`, zero `engine/api/db`.
2. Codex resolve os itens **1** e **2** e finaliza `radar_time_v0`.
3. Codex sobe **PR #2** (contrato + `engine/radar_time.py` + parser CBF + ingestão).
4. Claude reconcilia `web/lib/types.ts` + `web/lib/mock.ts` + `web/components/TeamRadar.tsx`
   ao contrato final. (Não antes — evita retrabalho enquanto o contrato é "proposto".)
