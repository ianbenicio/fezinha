# Especificação do Fezinha

## Estrutura

- `contract-engine-api-web-v0.md` — Contrato minimo e retrocompativel entre motor, API e web
- `secoes-28-35-upgrades.md` — Mudanças de design recomendadas para a v3 da arquitetura
- `secao-36-propriedades-camadas.md` — Propriedades obrigatorias para contratos de camada

## Fluxo de Integração

1. **Documento mestre original** (não incluído aqui — mantido fora do repo por estar em evolução)
2. **Seções 1-27** — Arquitetura base (existe em referência, versão 2.0)
3. **Seções 28-35** (`secoes-28-35-upgrades.md`) — Upgrades v3:
   - **Seção 28:** Revisão do núcleo estatístico
     - Troca Elo → pi-ratings
     - Dixon-Coles com requisitos (rho, ξ, blend xG)
     - Remoção de variáveis redundantes
     - Shrinkage bayesiano
   - **Seção 29:** Agregador otimizado
     - Stacking multinomial logit
     - Calibração isotônica
     - Validação walk-forward
   - **Seção 30:** Moneyball — impacto individual
     - Metodologia above replacement
     - Métricas: xG+xA (nível 1) → xT (nível 2) → VAEP (nível 3)
     - Pipeline escalação → ajuste Dixon-Coles
   - **Seções 31-34:** 4 camadas novas
     - H2H (histórico direto, peso baixo, em prova)
     - Fatos relevantes (qualitativo, ajusta incerteza)
     - Visão das casas (sinal editorial, sem odds)
     - Visão do time (antecipado vs consumido)
   - **Seção 35:** Arquitetura consolidada v3

## Regra de Ouro

Nenhuma camada lê output de outra. Cada camada produz seus números/sinais independentemente. Fusão acontece só no agregador final.

## Próximos Passos

1. Validar `contract-engine-api-web-v0.md` com o consumidor web
2. Implementar agregador fallback sem quebrar o contrato v0
3. Integrar seções 28-35 ao documento mestre
4. Implementar cada componente novo
5. Coletar histórico de previsões (~2 temporadas) para treinar stacking
6. Validação walk-forward e backtest

---

**Versão:** 3.0 (seções 28-35)  
**Data:** 2026-06-11
