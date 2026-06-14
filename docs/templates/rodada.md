# Template de preenchimento por rodada

O que o **ge não dá** e você envia manual: **odds** e **desfalques/escalação**.
(Resultados, tabela, escudos, datas → automáticos via `ge_globo.py`.)

Preencha os jogos da rodada, **cole no chat**, e eu insiro no banco de uma vez.
Formato livre — pode omitir o que não tiver. Eu normalizo.

---

## Formato

```
Rodada 19

Flamengo x Palmeiras
odds: casa 2.10 | empate 3.30 | visitante 3.20 | over2.5 1.85 | escanteios9.5 1.90
desfalques casa: Pedro (lesao), Pulgar (suspenso)
desfalques fora: Gustavo Gómez (duvida)

São Paulo x Corinthians
odds: casa 1.95 | empate 3.20 | visitante 4.00 | over2.5 2.05
desfalques casa: -
desfalques fora: Memphis (lesao)
```

## Regras
- **odds:** só os mercados que tiver. `over2.5` e `escanteios9.5` opcionais.
  Use a odd de UMA casa (de preferência a mesma sempre — ex. Betano).
- **desfalques:** `nome (motivo)`, motivo = `lesao` | `suspenso` | `duvida`.
  `-` ou em branco = sem desfalques.
- **time:** use o nome como aparece no app (ex. "Red Bull Bragantino" ou "Bragantino" — eu resolvo).
- Não precisa preencher placar/data — isso vem do ge.

## Por que isso importa
- **odds** → liga a camada de banca: cruza com a probabilidade do modelo,
  calcula EV e dá a recomendação (apostar / evitar / quanto).
- **desfalques** → camada `elenco_impacto`: ajusta a força do time para AQUELE
  jogo (peça-chave fora muda a previsão horas antes).

## Periodicidade
- Uma vez por rodada (idealmente 1-2 dias antes, com escalação provável saindo).
- Odds podem ser enviadas 2x: abertura + perto do jogo (alimenta movimento de mercado).
