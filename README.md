# Projeto Fezinha

Sistema de previsão de partidas de futebol usando agregador probabilístico multicamadas.

## Princípio Central

**Cada camada analisa independentemente. Nenhuma camada lê output de outra. Fusão só no agregador final.**

Evita dupla contagem de informação. Se odds refletem lesão e teu modelo contextual também conta — lesão pesa 3x. Independência garante cada sinal conta uma vez.

## Arquitetura v3

- **16 camadas** organizadas em 3 núcleos
- **Núcleo Estatístico:** pi-ratings, Dixon-Coles (com rho, decaimento temporal, blend xG), shrinkage bayesiano
- **Núcleo Contextual:** metadados, elenco (com impacto individual acima do substituto), tática, arbitragem, clima, H2H, fatos relevantes, visão do time
- **Núcleo Externo:** odds, movimento de mercado, consenso externo, visão das casas
- **Agregador:** stacking + calibração isotônica (fallback: pesos fixos)
- **Governança:** qualidade de dados, confiança, alertas, backtest walk-forward, poda automática

## Documentação

### `/docs/spec/`

- `secoes-28-35-upgrades.md` — Mudanças recomendadas vs documentação original (seções 28-35)
  - Seção 28: Núcleo estatístico revisado (pi-ratings, Dixon-Coles com requisitos, removal de redundância)
  - Seção 29: Agregador otimizado (stacking, calibração, walk-forward)
  - Seção 30: Moneyball — impacto individual above replacement
  - Seções 31-34: 4 camadas novas (H2H, Fatos Relevantes, Visão das Casas, Visão do Time)
  - Seção 35: Arquitetura consolidada v3

## Status

- [ ] Integrar seções 28-35 ao documento mestre da spec
- [ ] Implementar pi-ratings
- [ ] Implementar Dixon-Coles com 3 requisitos (rho, ξ, blend xG)
- [ ] Implementar stacking para agregador
- [ ] Calibração isotônica
- [ ] Backtest com validação walk-forward
- [ ] Coleta de dados: FBref (nível 1), event data (níveis 2-3)
- [ ] Poda automática de camadas por coeficiente nulo

## Referências

- Constantinou & Fenton (2013): pi-ratings — rating system for football
- Dixon & Coles (1997): Bivariate poisson models for football prediction
- Karlis & Ntzoufras: Bivariate poisson extensions
- Baio & Blangiardo: Hierarchical models for sports data
- Goddard (2005): Ordered logit models
- KU Leuven: VAEP, xT, socceraction
- FiveThirtyEight: SPI model (xG blend approach)
