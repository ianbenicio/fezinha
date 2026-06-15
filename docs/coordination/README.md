# Coordenacao do Projeto Fezinha

Status: ativo
Ultima revisao: 2026-06-15

Este diretorio e o ponto unico para coordenacao entre humano, Codex e Claude.
Ele nao substitui specs tecnicas nem documentacao de produto; ele aponta onde
cada decisao vive e qual arquivo deve ser consultado antes de alterar o fluxo.

## Fonte de verdade por assunto

| Assunto | Arquivo/branch | Observacao |
|---|---|---|
| Regras de trabalho paralelo | `docs/coordination/governanca-operacional.md` | Politica duravel de branches, locks, fases e gates. |
| Contrato engine -> api -> web v0 | `docs/spec/contract-engine-api-web-v0.md` | Shape aprovado para `/queries` e consumo web. |
| Catalogo de fontes | `docs/spec/source-catalog-v0.md` | Criterios para sites/fontes, entrada no banco e uso por modulo. |
| Requisitos do consumidor web | `claude/web-map:docs/contract-v0-requirements-web.md` | Documento do Claude; referencia de necessidades da UI. |
| Review do contrato pelo Claude | `claude/web-map:docs/reviews/contract-v0-review-claude.md` | Aprova `codex/contract-v0` commit `b50788b`. |
| Mapa atual do web | `claude/web-map:docs/web-map.md` | Inventario do frontend. |
| Handoff atual para Claude | `docs/coordination/handoff-claude-2026-06-15.md` | Resumo datado do estado integrado. |

## Estrutura esperada

```text
docs/
  coordination/
    README.md                         # este indice
    governanca-operacional.md         # regras e fases
    handoff-*.md                      # resumos datados entre agentes
  spec/
    README.md
    contract-engine-api-web-v0.md     # contrato tecnico versionado
  reviews/
    *.md                              # reviews quando forem trazidos para branch de integracao
  templates/
    rodada.md
```

## Regra de uso

- Se for decisao de processo, registrar em `docs/coordination/`.
- Se mudar payload, API, output de engine ou contrato de camada, registrar em
  `docs/spec/` e exigir review do consumidor/produtor.
- Se for review de outro agente, manter em `docs/reviews/` quando a branch de
  integracao trouxer o arquivo.
- Se for estado temporario de sessao, registrar como handoff datado e tambem no
  Engram, com `author` correto.

## Branches locais relevantes em 2026-06-15

| Branch/worktree | Estado | Uso |
|---|---|---|
| `main` | base local igual a `origin/main` no ultimo fetch conhecido | Base de integracao. |
| `codex/contract-v0` | contrato v0 escrito; review Claude aprovado por referencia | Base recomendada para Fase 1B. |
| `codex/forca-config-isolation` | corrige isolamento de `forca_comparativa` | Deve ser integrado antes ou junto da Fase 1B. |
| `codex/manual-data-intake` | validacao de intake manual | Util para fluxo de dados manuais. |
| `claude/web-map` em `C:\Users\ianfl\Documents\fezinha-claude` | UI, mock, `/preview`, review do contrato | Nao misturar manualmente sem branch de integracao. |

## Artefatos locais que nao devem entrar

- `web/tsconfig.tsbuildinfo`
- `.next/`
- `node_modules/`
- arquivos temporarios de preview que sejam apenas do ambiente local

Se algum desses aparecer em `git status`, nao stagear.
