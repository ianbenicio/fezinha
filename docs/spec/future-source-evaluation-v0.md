# Avaliacao de fontes futuras v0

Status: proposto
Versao: v0
Data: 2026-06-15
Base: `docs/spec/source-catalog-v0.md`

## Objetivo

Registrar avaliacao inicial de fontes que nao devem ser ligadas agora sem
decisao humana, custo aprovado ou schema de staging.

## API-Football

Status: `futuro`

Fonte oficial consultada:

- `https://www.api-football.com/pricing`
- `https://www.api-football.com/documentation-v3`

Fatos verificados em 2026-06-15:

- plano gratuito existe, mas e limitado em requisicoes diarias;
- planos pagos existem e aumentam o limite diario;
- a pagina de preco lista endpoints como fixtures, lineups, injuries,
  pre-match odds, in-play odds, statistics e predictions;
- a propria pagina informa que planos gratuitos sao limitados nas temporadas
  disponiveis.

Uso recomendado no Fezinha:

- `futuro` para elenco, escalacao, lesao, stats de partida/jogador e possivel
  odds, depois de testar cobertura real do Brasileirao 2026;
- nao usar para substituir CBF em placar/calendario oficial quando CBF estiver
  disponivel;
- nao ligar em producao sem chave em ambiente, controle de cota e staging.

Pendencias antes de promover:

- testar cobertura da Serie A e Serie B 2026;
- confirmar se xG existe para os campeonatos desejados, porque isso nao deve
  ser presumido pelo nome generico `statistics`;
- medir custo por rotina diaria;
- definir quais endpoints entram no banco e quais ficam em cache;
- validar termos de uso para armazenamento e exibicao.

## Open-Meteo

Status: `futuro`

Fonte oficial consultada:

- `https://open-meteo.com/en/docs`

Fatos verificados em 2026-06-15:

- API de previsao meteorologica usa latitude/longitude;
- documentacao lista previsao padrao de 7 dias e possibilidade de ate 16 dias;
- documentacao lista variaveis horarias como temperatura, precipitacao,
  probabilidade de precipitacao, vento e rajadas.

Uso recomendado no Fezinha:

- `futuro` para camada clima;
- precisa de coordenadas canonicas por estadio;
- usar como alerta/contexto, nao como peso forte no agregador antes de backtest.

Pendencias antes de promover:

- criar catalogo de estadios com latitude/longitude;
- definir janela de coleta por jogo;
- validar impacto empirico de chuva/vento no Brasileirao;
- decidir se clima aparece apenas como alerta ou entra como modificador.

## Sites de palpite

Status: `quarentena`

Uso recomendado:

- nao alimentar agregador, banca, probabilidade ou radar numerico;
- podem ser monitorados como sinal editorial separado somente depois de
  backtest cego;
- sem prova empirica, sao ruido plausivel.

Pendencias antes de qualquer promocao:

- coletar palpites com timestamp antes do jogo;
- medir acuracia e calibracao por mercado;
- comparar contra baseline simples e odds;
- separar texto editorial de dado factual;
- revisar termos de uso.
