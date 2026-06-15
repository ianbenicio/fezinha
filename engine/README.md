# Motor Fezinha (`engine/`)

Núcleo de análise que transforma uma partida em probabilidades por mercado.
Implementação dos contratos de `../layers/` em Python.

## Estado atual: núcleo estatístico ativo

| Módulo | Papel | Status |
|--------|-------|--------|
| `dixon_coles.py` | matriz de placar → 1X2, Over/Under, BTTS, escanteios | ✅ |
| `strength.py` | estima λ (gols esperados) por time | ✅ baseline |
| `run.py` | orquestra e monta a saída no formato do agregador | ✅ |
| `radar_time.py` | gera radar explicativo por time a partir de lote CBF validado | ✅ local |
| `test_dixon_coles.py` | sanity checks (6 testes) | ✅ 6/6 |

## Como funciona

```
match + força dos times
  → strength.estimar_lambdas()  → λ_casa, λ_fora
  → dixon_coles.mercados_de_gols(λ_casa, λ_fora)
       matriz de placar 11×11 (com correção rho)
       → soma células → 1X2, Over 0.5/1.5/2.5/3.5, BTTS, placar provável
  → dixon_coles.mercados_de_escanteios()  → Over 8.5/9.5/10.5
```

## Rodar testes

```bash
python -m engine.test_dixon_coles
```

## Pendente (próximas camadas a portar)

O motor hoje usa **força baseline** (1.0 = média da liga) quando `teams.caracteristicas`
está vazio — a ingestão precisa popular ataque/defesa reais.

Camadas ainda em YAML, a portar:
- **pi_ratings** — ratings casa/fora reais (substituir força baseline)
- **elenco_impacto** — ajusta λ pela escalação (above replacement)
- **contexto_competitivo, clima, arbitragem** — modificadores de intensidade
- **odds, movimento_mercado** — camada de mercado
- **agregador** — stacking + calibração (funde tudo; hoje só o núcleo opina)
- **banca** — EV + Kelly (precisa de odds + prob calibrada)

Enquanto o agregador completo não existe, a saída traz `indice_confianca: null`
e o alerta `MOTOR_PARCIAL`. As probabilidades são do núcleo estatístico apenas.

## Radar por time

`radar_time.py` gera payload `radar_time_v0` a partir de lote
`manual_source_batch_v0`. O radar é explicativo e não alimenta o agregador,
EV, stake ou recomendação.

```bash
python -m engine.test_radar_time
```

## Sem dependências externas

Math puro (`math`). Quando entrarem otimização de pesos (stacking) e calibração,
aí sim numpy/scikit entram — em `requirements` próprio.
