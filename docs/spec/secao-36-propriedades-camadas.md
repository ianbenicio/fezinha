# Seção 36 — Propriedades de Camada (Contrato Anti-Generalização)

## 36.1 Princípio

Toda camada é um **contrato fechado**, não um prompt aberto. Camada sem contrato devolve análise genérica (estilo blog de aposta). O contrato força foco: cada camada responde UMA pergunta, usa inputs definidos, e devolve saída com schema travado.

Quatro propriedades matam generalização:

1. **`pergunta_unica`** — a camada responde uma pergunta específica, nunca "analise o jogo".
2. **`fora_de_escopo`** — lista explícita do que NÃO é problema da camada (reforça a regra de ouro: sem dupla contagem).
3. **`output_schema` travado** — enums + números + listas curtas + 1 campo de leitura. Impossível devolver ensaio.
4. **`exige_evidencia`** — toda afirmação ancora em fonte. Sem fonte → marcada como baixa confiança, não descartada.

## 36.2 Schema de propriedades (padrão)

Todo arquivo `layers/<id>.yaml` segue este padrão:

```yaml
# IDENTIDADE
id:                    # slug único da camada
nucleo:                # estatistico | contextual | externo | governanca
motor:                 # formula | llm | hibrido
versao:                # versão do contrato

# FOCO (anti-generalização)
pergunta_unica:        # a única pergunta que a camada responde
escopo:                # lista do que a camada PODE tratar
fora_de_escopo:        # lista do que a camada NÃO trata (delega)

# CONTRATO DE DADOS
inputs_permitidos:     # fontes/dados que a camada pode usar
inputs_proibidos:      # sempre inclui: odds, output de outras camadas (regra de ouro)
fonte_minima:          # nº mínimo de fontes verificáveis
janela_temporal:       # quão recente o dado precisa ser

# SAÍDA (schema travado)
output_schema:         # estrutura obrigatória do retorno
campo_leitura:         # único campo de texto livre; máx ~50 palavras; exige evidência
output_proibido:       # o que a saída NUNCA contém
max_output_tokens:     # teto duro

# ANTI-GENERALIZAÇÃO
exige_evidencia:       # true → toda afirmação cita fonte
sem_evidencia:         # marcar_baixa_confianca (não descarta)
proibe_especulacao:    # true → sem "pode ser", "talvez", "parece"
granularidade:         # especifica → "Pedro fora 3 jogos", não "alguns desfalques"

# GOVERNANÇA
peso_inicial:          # baixo | medio | alto (ponto de partida; stacking ajusta)
podavel:               # true → pode sair do agregador se coeficiente ~0
qualidade_min:         # nota mínima (0-5) para a camada contar no agregador
modelo_llm:            # (só motor=llm) haiku | sonnet | opus | fable
```

## 36.3 Regra do campo de leitura

Camadas de LLM têm UM campo `leitura` de texto livre, com regras:

- máximo ~50 palavras
- toda afirmação dentro dele cita evidência da própria saída (`segundo [fonte]...`)
- proibido: opinião sem âncora, linguagem de certeza, generalização ("time motivado", "jogo difícil")
- obrigatório: específico e verificável ("técnico confirmou poupar 3 titulares para a final de quarta")

O resto da saída é enum/número/lista. O `leitura` existe só para capturar nuance que o schema não cobre — não para narrar.

## 36.4 Regra de evidência fraca

Afirmação sem fonte verificável NÃO é descartada. É marcada:

```yaml
flag: nao_verificado
qualidade_dados: <rebaixada em 1-2 pontos>
```

Entra na saída com peso reduzido. O stacking (seção 29) decide empiricamente se sinal não-verificado tem valor preditivo. Descartar na origem perderia sinal fraco antecipado (ex.: rumor de lesão que vira confirmação 2h depois).

## 36.5 Tabela das 16 camadas

| Camada | Núcleo | Motor | Pergunta única | Peso inicial |
|--------|--------|-------|---------------|-------------|
| pi_ratings | estatistico | formula | Qual a força relativa casa/fora? | alto |
| dixon_coles | estatistico | formula | Qual a distribuição de gols esperada? | alto |
| shrinkage | estatistico | formula | A amostra é grande o suficiente? | — (modifica) |
| ordered_logit | estatistico | formula | Sanity check 1X2 diverge? | — (fora agregador) |
| metadados | contextual | formula | Calendário/descanso/viagem favorece quem? | medio |
| elenco_impacto | contextual | hibrido | Quanto o lineup muda o λ? | alto |
| tatica_matchup | contextual | hibrido | O estilo de um anula o outro? | medio |
| arbitragem | contextual | formula | O árbitro infla cartões/pênaltis? | baixo |
| clima | contextual | formula | O clima reduz gols esperados? | baixo |
| h2h | contextual | formula | Há padrão direto após controlar força? | baixo |
| fatos_relevantes | contextual | llm | Há fato objetivo que muda a partida? | baixo |
| visao_time | contextual | llm | O clube sinaliza prioridade reduzida? | medio |
| odds | externo | formula | Qual a probabilidade implícita do mercado? | alto |
| movimento_mercado | externo | formula | O mercado comprou um lado? | medio |
| consenso_externo | externo | formula | As fontes externas concordam? | baixo |
| visao_casas | externo | llm | Sinal editorial/estrutural das casas? | baixo |

## 36.6 Validação do contrato

Antes de uma camada entrar em produção, validar:

- [ ] `pergunta_unica` é respondível com os `inputs_permitidos`?
- [ ] `inputs_proibidos` inclui `odds` e `output_outras_camadas`?
- [ ] todo campo do `output_schema` é enum/número/lista, exceto o único `leitura`?
- [ ] `fora_de_escopo` não tem sobreposição com o `escopo` de outra camada?
- [ ] motor `llm` tem `modelo_llm` definido e `max_output_tokens` < 1500?

Contrato que falha qualquer item não sobe.

---

**Versão:** 1.0
**Data:** 2026-06-11
