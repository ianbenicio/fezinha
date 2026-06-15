# Handoff para Claude - 2026-06-15

Autor: Codex
Escopo: sincronizacao local entre worktrees `fezinha` e `fezinha-claude`
Status: ativo

## Resumo curto

O contrato `engine -> api -> web v0` foi escrito por Codex no branch
`codex/contract-v0` e o Claude registrou review aprovado no branch
`claude/web-map`, referenciando o commit `b50788b`.

O proximo bloqueio real do lado Codex e implementar a Fase 1B:
agregador fallback executavel, sem inventar EV/banca quando odds estiverem
ausentes. O radar visual ainda depende do payload/shape de radar que Codex deve
entregar depois do fallback.

## Estado verificado localmente

| Item | Estado |
|---|---|
| Repo oficial Codex | `C:\Users\ianfl\Documents\fezinha` |
| Worktree Claude | `C:\Users\ianfl\Documents\fezinha-claude` |
| Branch Codex ativo para contrato | `codex/contract-v0` |
| Branch Claude | `claude/web-map` |
| Commit Claude dashboard | `56cbc2c feat(web): dashboard refinado + previewavel` |
| Commit Codex contrato | `b50788b feat: define engine api web contract v0` |
| Preview Claude | `http://localhost:3100/preview` respondeu `HTTP 200` nesta verificacao |

## Entregas Codex ja existentes

- `docs/spec/contract-engine-api-web-v0.md`
  - Define envelope de `POST /queries`.
  - Mantem retrocompatibilidade de `agregador.resultado`, `agregador.gols` e
    `agregador.escanteios`.
  - Define `agregador.modo` com `nucleo_apenas`, `modelo_only`,
    `fallback_pesos`.
  - Formaliza `indice_confianca`, `alertas`, `banca` e `trace`.
  - Declara `forca_comparativa` como explicativa nesta fase.
- `engine/test_contract_v0.py`
  - Testa shape minimo do payload atual contra o contrato v0.
- `engine/run.py`
  - Ajustado para expor os campos do contrato v0.
- `docs/coordination/governanca-operacional.md`
  - Define regras de trabalho paralelo, locks e fases.

## Entregas Claude verificadas

No branch `claude/web-map`:

- `docs/web-map.md`
- `docs/contract-v0-requirements-web.md`
- `docs/reviews/contract-v0-review-claude.md`
- `web/lib/types.ts`
- `web/lib/mock.ts`
- `web/components/states.tsx`
- `web/components/DashboardView.tsx`
- `web/app/preview/page.tsx`
- ajustes em `/consulta`, `/historico` e pagina inicial.

O review do Claude aprova o contrato do Codex e fecha o gate do consumidor web.

## Dependencias entre agentes

### Codex deve seguir agora

1. Integrar/confirmar o contrato v0 como base da Fase 1B.
2. Implementar agregador fallback executavel.
3. Preservar a regra: nenhuma camada le output de outra; fusao so no agregador.
4. Garantir que sem odds validas:
   - `banca.recomendacoes` fique vazia;
   - EV/stake nao sejam calculados por suposicao;
   - UI receba alerta/mensagem de indisponibilidade.
5. Depois disso, definir payload do radar.

### Claude pode seguir sem bloquear Codex

- Refinar componentes visuais ja mockados.
- Padronizar `Loading`, `EmptyState`, `ErrorState` em calendario, noticias e
  historico.
- Preparar componente de radar com mock local, desde que nao declare contrato
  real nem conecte no backend antes do payload Codex.

### Claude deve aguardar Codex

- Radar real.
- Modo real do radar no backend.
- Visual final de banca/EV caso dependa de odds ou agregador fallback ainda nao
  entregue.

## Arquivos e conflitos esperados

Baixo risco de conflito tecnico:

- Claude alterou principalmente `web/` e docs de review/mapa.
- Codex alterou `engine/`, `docs/spec/`, `.gitignore`, README e docs de
  coordenacao.

Risco de conflito conceitual:

- `docs/reviews/contract-v0-review-claude.md` esta no branch do Claude, nao no
  branch Codex atual.
- Em branch de integracao, trazer o review para `docs/reviews/` ou manter
  referencia explicita ao branch `claude/web-map`.

## Nao stagear

- `web/tsconfig.tsbuildinfo`
- `.claude/` se for apenas configuracao local de preview
- `.next/`
- `node_modules/`

## Proximo plano recomendado

1. Codex conclui Fase 1B em branch `codex/fallback-aggregator` ou continua a
   partir de `codex/contract-v0`, conforme decisao humana.
2. Depois, abrir branch de integracao local para combinar:
   - `codex/contract-v0`
   - `codex/forca-config-isolation`
   - `claude/web-map`
3. Rodar testes Python e build web.
4. So depois decidir push/PR.

## Limites deste handoff

- Nao afirma que o agregador fallback ja foi implementado.
- Nao afirma que radar real existe.
- Nao afirma que dados de odds, xG, escalacao ou lesoes estao automatizados.
- Nao faz push.
