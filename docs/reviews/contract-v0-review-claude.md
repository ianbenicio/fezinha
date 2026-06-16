# Review do contract-v0 — consumidor web (Claude)

- **Contrato revisado:** `docs/spec/contract-engine-api-web-v0.md`
- **Origem:** branch `codex/contract-v0`, commit `b50788b`
- **Revisor:** Claude Code (consumidor web)
- **Data:** 2026-06-15
- **Veredito: APROVADO** — fecha o gate §10 ("Claude revisa este contrato como consumidor web").

## Checagem vs requisitos (`docs/contract-v0-requirements-web.md`)

| Requisito | Contrato | Status |
|---|---|---|
| 1. Retrocompat de `agregador` (não renomear `resultado/gols/escanteios`) | §4 + teste `test_agregador_retrocompativel` | ✅ |
| 2. `agregador.modo` enum (`nucleo_apenas`/`modelo_only`/`fallback_pesos`) | §4.1, canônico + `meta.modo` espelhado | ✅ |
| 3. Formalizar `indice_confianca` / `alertas` / `banca` | §6/§7/§8, `valor:null` ok, `recomendacoes:[]` sem odds | ✅ |
| 4. status/qualidade por camada no `trace` | §9, status + `qualidade 0..5` | ✅ |
| 5. Autoridade da `forca_comparativa` decidida | §5 — **explicativa**; `agregador.resultado` é a previsão; IFC não compete visualmente | ✅ |

## Bônus do contrato (adotados no web)
- `agregador.meta.camadas_ativas` / `camadas_pendentes` → alimenta estado "camada pendente".
- `alertas[].severidade` (`info`/`aviso`/`bloqueio`) → cor do alerta.
- `trace.status` expandido (`dado_ausente`/`fonte_vencida`/`erro`) + `trace.fonte_ausente` → casa com `MissingData`/`StaleSource`.

## Notas não-bloqueantes (não travam o fallback)
1. Envelope `POST /queries` agora é `{query_id, custo_creditos, resultado}`. O web lê só `r.resultado` (ignora os 2 novos, sem quebra). Ampliar o tipo do `apiPost` quando for exibir `custo_creditos`.
2. `forca_comparativa.leitura` / `mandante.leitura` são `string` livres — o web mapeia `vantagem_*` por dicionário com fallback. Documentar os valores quando possível.
3. `test_forca_comparativa` cobre só o caso `null` (baseline). Quando a força existir, vale teste do caso populado (futuro).

## Reconciliação aplicada no web (commit `54d06a8`)
`web/lib/types.ts`, `web/lib/mock.ts`, `web/components/states.tsx` alinhados ao contrato:
`CamadaStatus` 6 valores, `agregador.modo`+`meta` obrigatórios, `alerta.severidade`,
`forca.ajustes_aplicados`, `top3_placares`, `gols.over_05`, topo `_stub/fonte/complexidade/mercados/lambdas`.
`/consulta` passou a renderizar modo/confiança/alertas/banca (commit `2cc6957`).

## Consequência
Gate §10 satisfeito. **Codex liberado para implementar o agregador fallback (Fase 1B).**
