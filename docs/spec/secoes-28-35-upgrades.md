# Projeto Fezinha — Seções 28 a 35

Adicionar após a seção 27 do documento mestre.

---

## 28. Revisão do Núcleo Estatístico

O Modelo Estatístico Próprio (seção 19.1) passa a adotar as seguintes mudanças, baseadas em literatura validada de previsão esportiva.

### 28.1 Substituição do Elo por pi-ratings

O Elo genérico é substituído pelo sistema **pi-ratings** (Constantinou & Fenton, 2013), desenvolvido especificamente para futebol.

Diferenças em relação ao Elo:

* mantém dois ratings por time: desempenho como mandante e desempenho como visitante
* incorpora margem de vitória com retornos decrescentes (4-0 atualiza mais que 1-0, mas não 4x mais)
* taxas de aprendizado separadas para resultado recente e tendência de longo prazo

O Glicko deixa de gerar probabilidade. Passa a ser usado apenas como **medida de incerteza de rating** (desvio), alimentando a Camada de Qualidade dos Dados e o Índice de Confiança. Times promovidos ou em início de temporada terão desvio alto, o que reduz a confiança final automaticamente.

### 28.2 Dixon-Coles como espinha dorsal, com três requisitos obrigatórios

O modelo Poisson/Dixon-Coles permanece como núcleo, mas só é considerado válido quando implementado com:

1. **Parâmetro rho (ρ):** correção de dependência em placares baixos (0-0, 1-0, 0-1, 1-1). Sem ele, o modelo subestima empates.
2. **Decaimento temporal (ξ):** peso exponencial por data do jogo. Jogos recentes pesam mais. Faz parte do paper original (1997) e é obrigatório.
3. **xG como input (blend):** as taxas de ataque e defesa de cada time são estimadas a partir de:

```
GolsAjustados = 0.70 * xG + 0.30 * GolsReais
```

Justificativa: gols são amostra ruidosa (~2,6 por jogo); xG é mais estável. O blend preserva informação de finalização real sem deixar o ruído dominar.

### 28.3 Remoção de variáveis redundantes

Ficam **removidas** do Modelo Estatístico Próprio:

* forma recente (V/E/D dos últimos jogos)
* aproveitamento recente
* xG/xGA como variável paralela

Motivo: o decaimento temporal do Dixon-Coles já captura momento. Manter forma recente como variável separada conta o mesmo sinal duas vezes (contaminação interna). O xG deixa de ser variável paralela porque vira o combustível do próprio Dixon-Coles (28.2).

A leitura qualitativa de momento (time em crise, embalo, pressão da torcida) pode existir, mas **apenas no Modelo Contextual**, nunca como número no estatístico.

### 28.4 Shrinkage bayesiano

Times com poucos jogos na amostra (promovidos, início de temporada, pós-janela com elenco reformulado) têm seus parâmetros de ataque e defesa puxados em direção à média da liga, proporcionalmente ao tamanho da amostra.

Regra prática:

```
ParametroFinal = w * ParametroEstimado + (1 - w) * MediaDaLiga
w = n / (n + k)
```

onde `n` é o número de jogos na janela e `k` é uma constante de regularização (calibrar via backtest; ponto de partida: k = 8).

Efeito: evita que um promovido com 3 jogos bons receba rating de candidato a título.

### 28.5 Modelo de comparação (sanity check)

Manter um **ordered logit** simples (Goddard, 2005) prevendo 1X2 diretamente a partir dos pi-ratings, sem passar por gols. Não entra no agregador. Serve apenas como verificação: se Dixon-Coles e ordered logit divergirem fortemente em um jogo, gerar `ALERTA_DIVERGENCIA_INTERNA`.

---

## 29. Agregador Otimizado

Os pesos fixos da seção 25 (0.55 / 0.30 / 0.15 e 0.65 / 0.35) deixam de ser a regra principal e passam a ser **fallback documentado**.

### 29.1 Princípio

Pesos de combinação não são opinião. São parâmetros a serem **aprendidos contra resultados históricos**, minimizando Log Loss.

### 29.2 Método: stacking

1. Cada camada produz suas probabilidades de forma independente (regra de ouro mantida).
2. Uma **regressão logística multinomial** recebe os outputs de todas as camadas como features e aprende os pesos ótimos.
3. Os coeficientes aprendidos são auditáveis: dizem objetivamente quanto cada camada contribui.

Regra de poda: se uma camada receber coeficiente próximo de zero de forma estável em múltiplas janelas de validação, ela é **removida do agregador** (continua sendo calculada e registrada para auditoria, mas não pesa na probabilidade final).

Evolução futura: substituir a regressão logística por gradient boosting (XGBoost/CatBoost) sobre os mesmos inputs, somente quando houver histórico suficiente (mínimo ~2 temporadas completas de previsões registradas).

### 29.3 Calibração final

Após o stacking, aplicar **isotonic regression** (ou Platt scaling) sobre as probabilidades combinadas. Objetivo: previsões de 60% devem vencer perto de 60% das vezes. A calibração é verificada na rotina de backtest (seção 24).

### 29.4 Validação walk-forward (regra adicional à seção 24)

Toda otimização de pesos e calibração deve usar validação temporal:

* treinar em temporadas/rodadas passadas, testar nas seguintes
* **nunca** embaralhar jogos aleatoriamente (vaza informação do futuro)
* re-treinar pesos a cada N rodadas (ponto de partida: N = 10)

### 29.5 Fallback

Enquanto não houver histórico suficiente para o stacking, valem os pesos fixos da seção 25. A saída deve registrar qual modo está ativo:

```
Agregador:
- modo: "stacking" | "pesos_fixos_fallback"
- pesos_em_uso: {...}
- data_ultimo_treino:
```

### 29.6 Ajuste no Índice de Confiança

A "Distância Probabilística" (seção 21) é complementada pela **entropia** da distribuição final, que captura os três resultados de uma vez:

```
Entropia = -(pC*ln(pC) + pE*ln(pE) + pV*ln(pV))
```

Entropia baixa = distribuição concentrada = mais confiança. Normalizar para 0-1 e usar no lugar do componente DistanciaProbabilistica, mantendo o mesmo peso (0.15).

---

## 30. Camada de Impacto Individual — Metodologia de Valor de Jogador

Esta seção substitui e aprofunda o tratamento de desfalques da camada de Elenco/Escalação. Princípio importado da sabermetria (Moneyball), adaptado: **medir contribuição real para o resultado, não estatística visível**.

Esta NÃO é uma camada nova. É a metodologia interna da camada de Elenco, Escalação e Jogadores. Criar camada separada violaria a regra de independência (usaria os mesmos dados duas vezes).

### 30.1 Métrica de contribuição

Cada jogador recebe um valor de contribuição por 90 minutos, em ordem de preferência conforme disponibilidade de dados:

| Nível | Métrica | Fonte | Custo |
|-------|---------|-------|-------|
| 1 (mínimo) | share de xG + xA do time, por 90 min | FBref (grátis) | zero |
| 2 (bom) | xT (Expected Threat) — valor de progressão de bola por zona | event data | médio |
| 3 (ideal) | VAEP — valor de cada ação (passe, drible, desarme) pela mudança na probabilidade de gol | event data (Opta/StatsBomb) | alto |

Implementação de referência para nível 2 e 3: biblioteca open-source `socceraction` (KU Leuven).

Começar no nível 1. Subir de nível apenas quando o backtest justificar o custo do dado.

### 30.2 Conceito central: valor acima do substituto (above replacement)

O impacto de um desfalque NÃO é o valor absoluto do jogador ausente. É a **diferença entre ele e quem joga no lugar**:

```
ImpactoDesfalque = Contribuicao(titular) - Contribuicao(substituto provável)
```

Exemplo:

```
Pedro: 0.45 contribuição/90
Substituto: 0.20 contribuição/90
Impacto real: -0.25 (não -0.45)
```

Consequência: desfalque de estrela com reserva forte pode valer menos que desfalque de jogador "invisível" sem reposição (ex.: único volante que organiza a saída de bola).

### 30.3 Pipeline: escalação confirmada → ajuste no modelo

```
1. Escalação confirmada (ou provável) divulgada
2. Somar contribuição esperada dos 11 titulares
   (ajustada por minutos jogados e força dos adversários enfrentados)
3. Calcular delta vs lineup "base" do time
   (lineup base = 11 mais frequentes da janela recente)
4. Converter delta em ajuste percentual no λ (taxa de gols)
   do Dixon-Coles para aquele jogo específico
```

A fórmula de conversão delta→λ é parâmetro do backtest. Ponto de partida conservador: cap de ±15% no λ por jogo.

### 30.4 Regra de independência preservada

Este ajuste no λ acontece **dentro do Modelo Próprio**, antes do agregador. A camada de odds e o consenso externo continuam sem acesso a este cálculo, e vice-versa.

### 30.5 Leitura de mercado (a verdadeira lição do Moneyball)

O mercado de odds tende a reagir forte a desfalques **visíveis** (artilheiro, camisa 10) e fraco a desfalques **estruturais** (volante de saída de bola, zagueiro que constrói).

Sinal de valor: quando o ImpactoDesfalque calculado divergir da reação do mercado (movimento de odds), registrar:

```
ALERTA_DESFALQUE_SUBPRECIFICADO:
- jogador:
- impacto calculado:
- movimento de mercado observado:
- leitura: mercado reagiu mais/menos que o modelo
```

Esta divergência é candidata número um a edge real do sistema.

---

## 31. Camada — Histórico de Confrontos Diretos (H2H)

### 31.1 Aviso metodológico (registrado no documento)

Evidência acadêmica para valor preditivo de H2H é fraca. Após controlar a força atual dos times, o histórico de confrontos agrega pouco: amostras pequenas (5-10 jogos), elencos e técnicos diferentes a cada temporada.

Por isso esta camada nasce com **peso baixo e prazo de prova**: se o stacking (29.2) atribuir coeficiente próximo de zero por duas janelas de validação consecutivas, a camada é podada do agregador.

### 31.2 Pode usar

* resultados dos últimos confrontos diretos (janela máxima: 5 anos)
* placares e local de cada confronto
* padrões recorrentes objetivos (ex.: time X nunca venceu no estádio Y nos últimos N jogos)
* contexto tático recorrente do confronto, somente se os técnicos forem os mesmos

### 31.3 Não pode usar

* odds
* palpites externos
* probabilidades de outras camadas
* jogos com mais de 5 anos
* confrontos em competições de natureza muito diferente (amistoso vs final)

### 31.4 Regras de qualidade

* menos de 4 confrontos na janela → qualidade de dados máxima 2
* elencos com menos de 40% de sobreposição com o último confronto → reduzir qualidade em 1 ponto
* técnico diferente em qualquer um dos lados desde o último confronto → registrar como limitação

### 31.5 Saída

```
CamadaH2H:
- ProbCasa:
- ProbEmpate:
- ProbVisitante:
- jogos considerados:
- padrão identificado:
- qualidade dos dados: 0 a 5
- limitações:
```

---

## 32. Camada — Fatos Relevantes

Captura eventos objetivos e verificáveis que afetam a partida e não pertencem a nenhuma outra camada.

### 32.1 Pode usar

* troca de técnico (data, jogos sob o novo comando)
* crise institucional documentada (salários atrasados, protesto de torcida)
* maratona de jogos / viagem internacional no meio da semana
* decisão judicial, punição, perda de mando de campo
* jogo com portões fechados
* eliminação ou classificação recente com impacto emocional documentado
* estreia de reforço relevante

### 32.2 Não pode usar

* rumor sem fonte verificável
* opinião editorial ("time x está mais motivado")
* odds, palpites externos, outputs de outras camadas
* fatos já capturados por outra camada (lesão → camada de elenco; calendário → contextual)

### 32.3 Regra anti-sobreposição

Antes de registrar um fato, verificar se ele já é input de outra camada. Cada fato pertence a exatamente UMA camada. Em caso de dúvida, o fato fica nesta camada e a outra camada não o usa.

### 32.4 Formato de cada fato

```
Fato:
- descrição:
- fonte:
- data:
- direção do impacto: pró-mandante | pró-visitante | neutro | aumenta incerteza
- magnitude estimada: baixa | média | alta
```

### 32.5 Saída

Esta camada NÃO gera probabilidades. Gera **ajuste de incerteza e leitura**:

```
CamadaFatosRelevantes:
- fatos: [...]
- leitura agregada:
- impacto na confiança: reduz | neutro | aumenta
- qualidade dos dados: 0 a 5
```

Fatos com direção "aumenta incerteza" alimentam diretamente o ALERTA_JOGO_INSTAVEL (seção 22).

---

## 33. Camada — Visão das Casas de Apostas

### 33.1 Definição operacional (obrigatória para evitar dupla contagem)

Esta camada NÃO usa odds nem movimento de odds — isso já pertence à camada de mercado existente. Usar números de odds aqui contaria a mesma informação duas vezes.

Esta camada captura apenas o **conteúdo editorial e estrutural** das casas:

### 33.2 Pode usar

* análises editoriais publicadas pelas próprias casas (blogs, prévias oficiais)
* destaques e promoções específicas para a partida (jogo promovido = casa espera volume)
* mercados oferecidos ou suspensos (suspensão de mercado = casa incerta sobre informação)
* limites de aposta praticados, quando observáveis (limite baixo = casa desconfiada da própria linha)
* boosts e super odds (indicam onde a casa aceita risco)

### 33.3 Não pode usar

* valores de odds (camada de mercado)
* movimento de odds (camada de mercado)
* palpites de sites externos (camada de consenso)
* outputs de outras camadas

### 33.4 Saída

```
CamadaVisaoCasas:
- leitura editorial dominante:
- sinais estruturais: [mercados suspensos, limites, boosts]
- direção: pró-mandante | pró-visitante | neutra | dividida
- qualidade dos dados: 0 a 5
- limitações:
```

Esta camada não gera probabilidades numéricas. Entra no agregador como sinal categórico de direção e alimenta o Índice de Confiança.

### 33.5 Cláusula de poda

Mesma regra da camada H2H: coeficiente persistentemente nulo no stacking → camada sai do agregador, permanece registrada para auditoria.

---

## 34. Camada — Visão do Time

### 34.1 Definição operacional

Captura sinais emitidos pelo próprio clube sobre como ele trata a partida. Somente declarações e ações **públicas e verificáveis**.

### 34.2 Pode usar

* declarações de técnico e diretoria sobre prioridade da partida ("vamos poupar", "jogo da nossa vida")
* poupar titulares confirmado ou sinalizado em coletiva
* viagem antecipada / concentração especial / logística diferenciada
* declaração explícita de foco em outra competição
* histórico do técnico em situações análogas (costuma poupar antes de decisão?)

### 34.3 Não pode usar

* especulação da imprensa sem fala oficial
* odds, palpites externos, outputs de outras camadas
* escalação em si (camada de elenco) — aqui entra apenas a INTENÇÃO declarada antes da escalação sair

### 34.4 Relação com a camada de elenco

Esta camada é o **sinal antecipado**; a camada de elenco é a **confirmação**. Quando a escalação oficial sai, esta camada perde peso automaticamente (a informação foi consumida pela camada de elenco, que é mais confiável). Registrar:

```
status: "antecipado" (escalação não confirmada) | "consumido" (escalação confirmada)
```

Em status "consumido", a camada não entra no agregador daquela partida.

### 34.5 Saída

```
CamadaVisaoTime:
- mandante:
  - prioridade declarada: máxima | normal | reduzida | indefinida
  - sinais: [...]
- visitante:
  - prioridade declarada: máxima | normal | reduzida | indefinida
  - sinais: [...]
- status: antecipado | consumido
- qualidade dos dados: 0 a 5
```

---

## 35. Arquitetura Consolidada v3

A arquitetura final passa a ser:

### Núcleo Estatístico (gera probabilidades)
1. pi-ratings (mandante/visitante separados)
2. Dixon-Coles com rho, decaimento temporal e blend de xG
3. Shrinkage bayesiano
4. Ordered logit (somente sanity check, fora do agregador)

### Núcleo Contextual (gera leituras e ajustes)
5. Metadados (calendário, descanso, viagem)
6. Elenco e Escalação, com Impacto Individual acima do substituto (seção 30) — ajusta λ do Dixon-Coles
7. Tática e matchup
8. Arbitragem e disciplina
9. Clima real do jogo
10. Histórico de confrontos diretos (peso baixo, em prova)
11. Fatos relevantes (ajusta incerteza)
12. Visão do time (sinal antecipado, consumido pela escalação)

### Núcleo Externo (gera probabilidades e sinais)
13. Odds de casas (probabilidade implícita, margem removida)
14. Movimento de mercado (abertura vs atual)
15. Consenso de fontes externas (em prova permanente no stacking)
16. Visão das casas de apostas (sinal categórico, sem números de odds)

### Governança
17. Qualidade dos dados por camada
18. Índice de Confiança (com entropia)
19. Alertas (incluindo ALERTA_DESFALQUE_SUBPRECIFICADO e ALERTA_DIVERGENCIA_INTERNA)
20. Agregador: stacking + calibração isotônica (fallback: pesos fixos da seção 25)
21. Backtest com validação walk-forward
22. Poda de camadas por coeficiente nulo

### Regras de ouro reafirmadas

1. Nenhuma camada lê output de outra camada. Fusão só no agregador.
2. Cada fato/sinal pertence a exatamente UMA camada.
3. Peso de camada é resultado de backtest, não de opinião.
4. Camada que não prova valor é podada do agregador, mas continua registrada.
5. Linguagem sempre probabilística (seção 27 permanece integral).
