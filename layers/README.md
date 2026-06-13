# Contratos de Camada (`layers/`)

Cada camada do Fezinha é um **contrato fechado** em YAML. Objetivo: foco e direcionamento, evitando generalização da informação.

Padrão completo: [`docs/spec/secao-36-propriedades-camadas.md`](../docs/spec/secao-36-propriedades-camadas.md)

## Status: 18 camadas de análise + 6 módulos de governança/decisão — todos definidos

Pipeline completo: análise (18 camadas) → fusão (qualidade → agregador → confiança → alertas) → decisão (banca) → aprendizado (checagem_resultados).

### Núcleo Estatístico (lente: força/distribuição)
| Arquivo | Camada | Motor | Papel |
|---------|--------|-------|-------|
| `perfil_liga.yaml` | Perfil de Liga | formula | prior de calibração (multiligas-ready) |
| `pi_ratings.yaml` | pi-ratings | formula | força casa/fora por mercado |
| `dixon_coles.yaml` | Dixon-Coles + Poisson escanteios | formula | fábrica de mercados (1X2, O/U, BTTS, tempo, escanteios) |
| `shrinkage.yaml` | Shrinkage bayesiano | formula | regulariza amostra pequena |
| `ordered_logit.yaml` | Ordered logit | formula | sanity check (fora do agregador) |
| `forca_comparativa.yaml` | Força Comparativa | formula | rating transitivo Colley+Massey; IFC 0-100 |

### Bloco Contextual (lente: situacional/qualitativa)
| Arquivo | Camada | Motor | Papel |
|---------|--------|-------|-------|
| `metadados.yaml` | Metadados | formula | calendário/descanso/viagem |
| `contexto_competitivo.yaml` | Contexto Competitivo | híbrido (sonnet) | decisão/tabela/clássico → intensidade |
| `elenco_impacto.yaml` | Elenco/Impacto | híbrido (sonnet) | above replacement → ajusta λ (A EDGE) |
| `tatica_matchup.yaml` | Tática/Matchup | híbrido (sonnet) | estilo anula estilo |
| `arbitragem.yaml` | Arbitragem | formula | perfil do árbitro |
| `clima.yaml` | Clima | formula | condições no jogo |
| `h2h.yaml` | H2H | formula | retrospecto (peso baixo, em prova) |
| `fatos_relevantes.yaml` | Fatos Relevantes | llm (haiku) | fato objetivo que muda o jogo |
| `visao_time.yaml` | Visão do Time | llm (haiku) | clube sinaliza prioridade |

### Bloco Externo (lente: mercado)
| Arquivo | Camada | Motor | Papel |
|---------|--------|-------|-------|
| `odds.yaml` | Odds | formula | prob implícita sem margem (filtro favorito <1.4) |
| `movimento_mercado.yaml` | Movimento | formula | abertura vs atual = info nova |
| `consenso_externo.yaml` | Consenso | formula | sites de palpite (candidata a poda) |
| `visao_casas.yaml` | Visão das Casas | llm (haiku) | editorial/estrutural, sem números de odd |

### Governança de Fusão
| Arquivo | Módulo | Motor | Papel |
|---------|--------|-------|-------|
| `qualidade_dados.yaml` | Qualidade dos Dados | formula | nota 0-5 por camada; afeta confiança, não a prob |
| `agregador.yaml` | Agregador | formula | stacking + calibração isotônica; o único ponto de fusão |
| `indice_confianca.yaml` | Índice de Confiança | formula | quanto confiar na previsão (entropia + alinhamento) |
| `alertas.yaml` | Alertas | formula | registro central dos ALERTA_*; pode barrar entrada |

### Decisão / Aprendizado
| Arquivo | Módulo | Motor | Papel |
|---------|--------|-------|-------|
| `banca.yaml` | Gerenciamento de Banca | formula | EV + ½ Kelly + perfis de risco; recomenda e registra |
| `checagem_resultados.yaml` | Checagem / Feedback | híbrido (sonnet) | post-mortem por jogo; calibração mensal por lote |

## Mercados-alvo (decisão do dono)
1X2 · Over/Under gols (+ BTTS + mercados de tempo 1ºT/2ºT) · Escanteios O/U. Sem cartões nesta fase.

Cada camada produz output para todos os mercados pela sua lente. O agregador junta (stacking, §29).

## Princípio: lente por camada
Cada camada opina sobre cada mercado pela SUA lente; nenhuma lê a outra; o agregador funde. Contexto/subjetivo fica nas camadas analíticas — o núcleo estatístico é puro (não conhece motivação/situação).

## As 4 propriedades anti-generalização
1. **`pergunta_unica`** — uma pergunta por camada.
2. **`fora_de_escopo`** — o que delega (sem dupla contagem).
3. **`output_schema` travado** — enum/número/lista + 1 campo `leitura` (máx 50 palavras).
4. **`exige_evidencia`** — sem fonte → `marcar_baixa_confianca` (não descarta).

## Banca — perfis de risco
Eixo conservador → moderado (½ Kelly) → agressivo. Cada perfil define EV mínimo, fração Kelly, caps de exposição e política de múltiplas. Múltiplas permitidas mostrando prob combinada + perfil de risco. Modo: recomenda + registra (ROI/CLV real).

## Decisões de design (2026-06-11)
- Rigidez output: schema travado + 1 campo leitura curto com evidência
- Sem evidência: marca baixa confiança, não descarta
- Formato: doc (§36) define padrão + YAML por camada executa
- Mercados: 1X2 + O/U gols + escanteios
- Fase inicial: só Brasileirão; arquitetura multiligas-ready
- Métrica de jogador: sequência nível 1 (xG+xA grátis) → 2/3 (xT/VAEP) gated por backtest
- Banca: perfis de risco configuráveis, recomenda + registra
