# Seção de Times — estrutura (descrição de times + radar)

> **Estrutura/planejamento — não implementado ainda.** Acordado entre Claude (consumidor web)
> e Codex. Serve de alvo de mock pro web e de requisitos pros endpoints do Codex.
> O contrato técnico canônico do `radar_time` será fixado pelo Codex em `docs/spec/` quando implementado.

## Objetivo
Página de descrição de time: aspectos técnicos/estatísticos, jogadores, notícias e o **gráfico radar**.
Tudo **exploratório/explicativo** — não entra no agregador, não altera probabilidade, não vira aposta,
não promete acurácia. Registrável pra backtest futuro.

## Rota / IA
- `/times` — índice (grid de cards por time, filtro por liga).
- `/times/[teamId]` — detalhe (foco). Link "Times" na Nav.
- Entradas cruzadas: `/calendario` e `/consulta` → clicar no time leva ao detalhe.

## Blocos do detalhe (ordem) + disponibilidade de dado
| # | Bloco | Dado | Fonte | Status hoje | Provedor |
|---|---|---|---|---|---|
| 1 | Identidade | nome, escudo | `matches` (ge) | ✅ via `/catalog/matches` | web deriva (ideal: endpoint próprio) |
| 1 | Identidade | posição, pontos, forma | classificação ge.globo | 🟡 ingerido, sem API | **Codex: endpoint standings** |
| 2 | **Radar** | 6 eixos (ver abaixo) | CBF resultados (+CA/CV futuro) | 🟡 5/6 alimentáveis; calculável | **Codex: `radar_time` por time** |
| 3 | Estatísticas | ataque/defesa, IFC, médias, mando, over% | engine (Colley/Massey + strength + perfil) | 🟡 existe por-jogo, não standalone | **Codex: expor por time** |
| 4 | Elenco/jogadores | lista, stats, lesão/suspensão | `player_stats`/`player_status` (mig. 006/007) | 🔴 vazio (fonte paga) | placeholder · API-Football PRO |
| 5 | Jogos | próximos + últimos do time | `matches` | ✅ filtra por time | web |
| 6 | Notícias do time | notícias | `news` (ge) | 🟡 só por liga, sem tag de time | placeholder + filtro aproximado por nome |

## Radar — 6 eixos MVP (todos `resultado`)
| Eixo (id) | Label | O que mostra | Processamento | Dado hoje |
|---|---|---|---|---|
| `forca_ofensiva` | Ataque | produzir gols | gols pró/jogo + últimos 5/10, normalizado na liga | ✅ CBF |
| `solidez_defensiva` | Defesa | evitar gols | inverso gols contra/jogo + clean sheets, normalizado | ✅ CBF |
| `forma_recente` | Forma | resultado recente | últimos 5 com peso 30/25/20/15/10 | ✅ CBF/ge |
| `consistencia` | Consistência | previsibilidade | inverso do desvio do saldo/pontos (últimos 10) | ✅ CBF |
| `contexto_casa_fora` | Casa/Fora | rendimento no contexto | split casa (mandante) / fora (visitante), com shrinkage | ✅ CBF |
| `controle_disciplinar` | Disciplina | risco disciplinar | inverter `CA + 3*CV` por jogo (alto = mais controlado) | 🔴 **não ingerido** |

**Disciplina fica no shape, apagada** (`status: dado_ausente`) até o Codex ingerir CA/CV agregado da CBF.
Não é dependência exclusiva da API-Football PRO (essa é só pra disciplina fina: por jogo/jogador, pendurados).

### Modelo de processamento
```text
valor_base   = estatística oficial normalizada 0-100
modificadores = eventos temporários (com fonte, validade, delta)
valor_atual  = valor_base + soma(modificadores)
valor_bruto  = valor_atual (antes do clamp)  # guardar p/ badges
valor_exibido = clamp(valor_atual, 0, 100)
```
`valor_bruto` fora de [0,100] → badge `pico` / `crise` / `volatilidade` / `alerta_disciplina`.
Shrinkage nos eixos de baixa amostra (consistência, casa/fora, e geral com 18 rodadas) — reusa a camada `shrinkage` do Codex.

### Contrato (alvo de mock — `radar_time`)
```ts
radar_time: {
  modo: "resultado";
  escala: { min: 0; max: 100 };
  time: { id: number; nome: string; escudo_url: string | null };
  contexto: "casa" | "fora" | "neutro";
  eixos: EixoRadar[];                 // os 6 acima, sempre na mesma ordem
  modificadores: Modificador[];
  sinais: ("pico" | "crise" | "volatilidade" | "alerta_disciplina")[];
}

EixoRadar = {
  id: string;                          // ex "forca_ofensiva"
  label: string;
  base: number | null;
  atual: number | null;
  delta: number | null;
  valor_bruto: number | null;
  qualidade: number;                   // 0-5
  status: "ok" | "baseline" | "dado_ausente" | "fonte_vencida" | "erro";
  janela: string;                      // ex "ultimos_10" | "temporada"
  referencia: { liga: string; temporada: number };
  fontes: string[];
  motivo_ausencia?: string;            // quando status != ok
}

Modificador = { eixo: string; delta: number; motivo: string; fonte: string; validade?: string }
```

Exemplo do eixo ausente (disciplina):
```json
{
  "id": "controle_disciplinar", "label": "Disciplina",
  "base": null, "atual": null, "delta": null, "valor_bruto": null,
  "qualidade": 0, "status": "dado_ausente", "janela": "temporada",
  "referencia": { "liga": "brasileirao_a", "temporada": 2026 },
  "fontes": [], "motivo_ausencia": "CA/CV ainda nao ingeridos da CBF"
}
```

### Duplo uso (mesmo `radar_time`)
- **Página do time:** `base` (perfil) vs `atual` (momento) sobrepostos.
- **Análise da partida:** `mandante.atual` (contexto casa) vs `visitante.atual` (contexto fora) sobrepostos.
- Componente único: `<TeamRadar teams={1|2} modo="perfil"|"confronto" />`.
- Tooltip por eixo: base, modificador, fonte, janela, qualidade.

## Endpoints que o Codex precisa criar
1. `GET /catalog/teams` — lista (id, nome, escudo, liga, posição, pontos).
2. `GET /catalog/teams/{id}` — detalhe: identidade + standings + força/IFC standalone + médias.
3. `radar_time` por time (no detalhe ou endpoint próprio).
4. (futuro) `GET /catalog/teams/{id}/players` — quando houver fonte paga.
5. (futuro) ingestão simples de CA/CV agregado da CBF → acende `controle_disciplinar`.

## Placeholders (honestidade)
- Reusa `web/components/states.tsx`: `MissingData`, `StaleSource`, `EmptyState`.
- Elenco → bloco "Elenco indisponível — requer fonte paga (API-Football PRO)".
- Notícias por time → rótulo "filtro aproximado por nome" até haver tag de time.
- Eixo disciplinar → apagado + tooltip "não ingerido ainda; fonte candidata CBF CA/CV".
- Nunca inventar jogador, cartão ou número sem fonte.

## Componentes (a construir depois, presentacionais + mock)
`TeamCard` (índice) · `TeamHeader` · `TeamRadar` · `TeamStats` · `TeamSquad` (placeholder) · `TeamMatches` · `TeamNews`.
Padrão `DashboardView`: presentacional, props-driven, previewável em `/preview` sem backend.

## Decisão
Radar e seção de times = **exploratórios/explicativos**. Fora do agregador. Sem aposta. Sem claim de acurácia.
Registráveis pra backtest futuro.
