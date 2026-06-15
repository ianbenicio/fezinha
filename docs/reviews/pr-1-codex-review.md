# Review Codex - PR #1 claude/web-map

Data: 2026-06-15
PR: `https://github.com/ianbenicio/fezinha/pull/1`
Branch revisado localmente: `origin/pr/1`
Revisor: Codex
Status: merge condicional

## Resumo

O PR #1 entrega valor real no `web/`: estados visuais, dashboard mock, tela de
times, radar SVG e documentacao de consumo. O escopo informado confere quase
todo: altera `web/` e `docs/`, mas tambem toca `.gitignore`.

Nao encontrei alteracao em `engine/`, `api/` ou `db/migrations/`.

O ponto bloqueante para merge limpo como source of truth e o contrato do radar:
o PR usa um shape mockado anterior ao `docs/spec/radar-time-v0.md` do Codex.
Se entrar assim em `main`, o web fica visualmente pronto, mas desalinhado com o
payload que o backend vai produzir.

## Findings

### 1. Radar mock nao bate com `radar_time_v0`

Severidade: alta para integracao, media para UI mockada.

Arquivos no PR:

- `web/lib/types.ts`
- `web/components/TeamRadar.tsx`
- `docs/ux/team-section.md`

O PR define:

- `RadarTime.modo: "resultado"`;
- `time.id: number`;
- `contexto: "casa" | "fora" | "neutro"`;
- `RadarEixo.status: CamadaStatus`;
- `janela: string`;
- `fontes: string[]`;
- `valor_bruto: number | null`;
- sem `schema_version`;
- sem `meta.entra_no_agregador`.

O contrato Codex define em `docs/spec/radar-time-v0.md`:

- `schema_version: "radar_time_v0"`;
- `team.id: string`;
- `team.liga: string`;
- `contexto: "geral" | "casa" | "fora"`;
- status: `ok`, `baixa_amostra`, `dado_ausente`, `quarentena`, `conflito`,
  `fonte_vencida`;
- `janela: { tipo, jogos }`;
- `fontes: { source_id, source_url, fetched_at, quality_score, status_fonte }[]`;
- `valor_bruto: Record<string, unknown>`;
- `meta: { uso: "explicativo", entra_no_agregador: false, fonte_base, fetched_at }`.

Risco:

- quando o endpoint real sair, o payload nao encaixa no tipo do web;
- a UI nao consegue mostrar fonte/janela/qualidade com proveniencia completa;
- estados como `baixa_amostra`, `quarentena` e `conflito` somem do radar.

Correcao recomendada:

- alinhar `web/lib/types.ts` ao `radar_time_v0`;
- atualizar `mockRadarTime` para gerar o shape canonico;
- atualizar `docs/ux/team-section.md` para apontar `docs/spec/radar-time-v0.md`
  como contrato vigente, nao futuro.

### 2. `TeamRadar` apaga qualquer status diferente de `ok`

Severidade: media.

No PR, `ausente(e)` retorna `true` quando `e.status !== "ok" || e.atual == null`.
Isso e correto para `dado_ausente`, mas errado para estados calculados com aviso,
como `baixa_amostra` ou possivelmente `fonte_vencida`/`conflito` quando houver
valor exibivel em quarentena.

Risco:

- eixo calculado com baixa amostra vira visualmente zero;
- o usuario pode ler fraqueza tecnica onde o problema era qualidade de fonte.

Correcao recomendada:

- considerar ausente somente quando `atual == null` ou `status === "dado_ausente"`;
- renderizar `baixa_amostra`, `quarentena`, `conflito` e `fonte_vencida` com
  aviso visual/tooltip, preservando valor quando houver.

### 3. `.gitignore` tera conflito pequeno com branch Codex

Severidade: baixa.

PR #1 adiciona:

- `*.tsbuildinfo`;
- `.claude/`.

Branch Codex adicionou:

- `var/ingestion/`.

Risco:

- conflito mecanico simples quando integrar `codex/contract-v0` depois do PR.

Correcao recomendada:

- manter todos os ignores:
  - `*.tsbuildinfo`;
  - `.claude/`;
  - `var/ingestion/`.

### 4. `docs/ux/team-section.md` ficou parcialmente stale

Severidade: baixa, mas cria confusao.

O documento diz "nao implementado ainda" e que o contrato canonico do
`radar_time` sera fixado depois. No estado atual, o PR ja implementa mock de UI,
e o contrato canonico ja existe no branch Codex.

Correcao recomendada:

- trocar o texto para "mock implementado no web; contrato canonico em
  `docs/spec/radar-time-v0.md`";
- remover o contrato TypeScript duplicado ou marcar explicitamente como
  obsoleto.

## Veredito

Nao fazer merge cego.

O PR #1 pode seguir como entrega visual se a prioridade for destravar preview,
mas para `main` como fonte de verdade eu recomendo exigir antes o ajuste do
shape do radar para `radar_time_v0`. O custo de corrigir agora e pequeno; o custo
de corrigir depois aparece quando Codex criar endpoint real e a UI estiver
tipada no formato antigo.

## Proximo passo recomendado para Claude

1. Ler `docs/spec/radar-time-v0.md` no branch Codex.
2. Atualizar `web/lib/types.ts` e `web/lib/mock.ts` para o shape canonico.
3. Ajustar `TeamRadar` para diferenciar `dado_ausente` de `baixa_amostra` e
   outros estados com valor.
4. Atualizar `docs/ux/team-section.md` para nao duplicar contrato antigo.
5. Revalidar build.

## Proximo passo recomendado para Codex

1. Manter `codex/contract-v0` sem merge do PR #1 por enquanto.
2. Depois do ajuste/review do Claude, preparar PR Codex com contrato, parser CBF,
   radar local e documentacao de fontes.
3. Resolver `.gitignore` preservando entradas dos dois branches.
