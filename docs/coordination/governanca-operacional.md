# Governanca Operacional do Projeto Fezinha

Status: ativo
Versao: v0.2
Ultima revisao: 2026-06-15
Escopo: coordenacao entre agentes, humanos e branches do projeto Fezinha

## 1. Objetivo

Este documento define como o projeto Fezinha deve ser conduzido quando houver trabalho paralelo entre Codex, Claude Code e humanos.

Ele deve ser seguido durante a evolucao do projeto e alterado quando a realidade do repositorio mudar. Alteracoes neste documento exigem revisao, porque ele define regras de coordenacao, ownership temporario, arquivos travados e gates de validacao.

Indice operacional deste diretorio:

- `docs/coordination/README.md` lista a fonte de verdade por assunto.
- `docs/coordination/handoff-*.md` guarda resumos datados entre agentes.

## 2. Principio central do Fezinha

O Fezinha e um sistema de previsao e analise de partidas de futebol baseado em camadas independentes.

Regra principal:

```text
Nenhuma camada le output de outra camada. Fusao so acontece no agregador final.
```

Implicacao pratica:

- odds nao entram no modelo estatistico;
- contexto nao altera a camada de odds;
- consenso externo nao recalibra o modelo antes do agregador;
- ajustes contextuais devem ser aplicados no agregador ou em modulo explicitamente definido;
- qualquer excecao precisa ser documentada e revisada.

## 3. Estado atual conhecido

Este documento parte do estado verificado em 2026-06-15:

- Projeto local oficial: `C:\Users\ianfl\Documents\fezinha`
- Remoto: `https://github.com/ianbenicio/fezinha.git`
- Branch base: `main`
- Motor estatistico possui nucleo ativo em `engine/`
- Testes existentes para `dixon_coles` e `forca_comparativa` passam localmente
- Agregador completo ainda nao esta implementado como fusao real
- `layers/agregador.yaml` existe como contrato
- `web/` existe, mas a execucao atual deve ser validada por build/run antes de ser declarada funcionando
- `web/tsconfig.tsbuildinfo` e artefato local e nao deve ser commitado

Se qualquer item acima mudar, atualizar este documento ou registrar ADR.

## 4. Autoridade e tomada de decisao

Nenhum agente tem ownership permanente da arquitetura.

Regra de autoridade:

```text
Quem propoe uma mudanca abre branch/PR ou documento.
Outro agente/humano revisa.
Depois de aprovado, o artefato versionado vira fonte da verdade.
```

Nao usar:

- "Claude define, Codex implementa" como regra fixa;
- "Codex decide arquitetura" como regra fixa;
- mudanca direta em `main`;
- contrato alterado sem revisor consumidor/produtor.

## 5. Papel recomendado por agente

### Codex

Foco principal:

- `engine/`
- `api/`
- `db/`
- testes
- backtesting
- integracao entre engine, API e contratos
- agregador fallback e agregador real
- validacao de isolamento entre camadas

Codex deve priorizar tarefas em que erro gera regressao tecnica, quebra de contrato ou inconsistencia matematica.

### Claude Code

Foco principal:

- `web/`
- UX
- radar visual
- telas de consulta
- microcopy de estado e incerteza
- documentacao de produto
- revisao de especificacao e coerencia de sistema

Claude deve priorizar tarefas em que clareza de uso, apresentacao e interpretacao pelo usuario sejam criticas.

### Humano responsavel

Decide quando houver conflito entre:

- velocidade vs confiabilidade;
- experiencia visual vs contrato tecnico;
- modelagem estatistica vs simplicidade operacional;
- manter uma camada vs podar por baixo valor.

## 6. Arquivos travados

Os arquivos abaixo exigem aviso previo e revisao mutua antes de edicao:

| Arquivo ou pasta | Motivo |
|---|---|
| `README.md` | fonte publica de status e direcao |
| `docs/spec/` | especificacao principal |
| `layers/_TEMPLATE.yaml` | padrao de todas as camadas |
| `layers/agregador.yaml` | ponto de fusao do sistema |
| `layers/forca_comparativa.yaml` | contrato sensivel a isolamento |
| `db/migrations/` | altera estado persistente |
| contrato `engine -> api -> web` | fronteira entre produtor e consumidor |
| arquivos de configuracao raiz | afetam todo o projeto |

Regra:

```text
Se a mudanca altera contrato, schema, pesos, output ou regra de camada, precisa de revisao.
```

## 7. Branches

Nao trabalhar direto na `main`.

Padrao:

```text
codex/<escopo-curto>
claude/<escopo-curto>
human/<escopo-curto>
```

Exemplos:

```text
codex/contract-v0
codex/fallback-aggregator
codex/backtest-expansion
claude/web-map
claude/radar-ui
claude/source-status-ui
```

Antes de iniciar:

```bash
git fetch origin
git status
git switch main
git pull --rebase origin main
git switch -c <branch>
```

Se houver arquivo local solto, decidir explicitamente:

- ignorar;
- remover;
- commitar;
- mover para backlog.

Nao incluir artefatos de build.

## 8. Contrato de tarefa

Toda tarefa em paralelo deve declarar:

```text
Agente:
Branch:
Objetivo:
Pode editar:
Nao pode editar:
Dependencias:
Criterio de pronto:
Revisor obrigatorio:
```

Exemplo:

```text
Agente: Codex
Branch: codex/contract-v0
Objetivo: definir payload engine -> api -> web v0
Pode editar: engine/, api/, docs/spec/contratos.md
Nao pode editar: web/ componentes finais, db/migrations/
Dependencias: estado atual de engine.run
Criterio de pronto: teste garante shape do payload
Revisor obrigatorio: Claude, como consumidor web
```

## 9. Fases do projeto

### Fase 0 - Higiene e sincronia

Objetivo: evitar conflito antes de construir.

Codex:

- ajustar `.gitignore` para artefatos locais;
- rodar testes existentes;
- confirmar status do Git;
- identificar arquivos soltos.

Claude:

- mapear `web/` em read-only;
- listar telas, componentes, chamadas de API e estados existentes;
- nao alterar contrato.

Gate:

- `main` limpa ou com pendencias explicitadas;
- artefatos de build ignorados;
- nenhum trabalho direto na `main`.

### Fase 1 - Contrato v0 e agregador fallback

Objetivo: criar fronteira executavel entre engine, API e web.

Codex:

- rascunhar contrato `engine -> api -> web v0`;
- implementar agregador fallback executavel;
- diferenciar modos `nucleo_apenas`, `modelo_only`, `fallback_pesos`;
- corrigir contratos que violem isolamento, especialmente `forca_comparativa.yaml`;
- adicionar testes de shape do payload.

Claude:

- revisar contrato como consumidor web;
- apontar campos necessarios para UI;
- criar mock aderente ao contrato;
- documentar estados de interface: motor parcial, camada pendente, dado ausente.

Gate:

- contrato versionado;
- teste automatizado do payload;
- web consegue consumir mock sem depender do engine completo;
- agregador fallback nao promete EV/banca real sem odds.

### Fase 2 - Radar exploratorio

Objetivo: criar radar util sem claim falso de acuracia.

Codex:

- gerar payload do radar a partir do contrato v0;
- registrar sinais `pico`, `crise`, `volatilidade` e `alerta_disciplina`;
- salvar sinais para backtesting futuro;
- testar modo comparativo e modo tendencia.

Claude:

- implementar componente visual do radar;
- criar painel de fontes, qualidade e modificadores;
- mostrar limitacoes do sinal;
- evitar texto que sugira acuracia validada.

Gate:

- radar funciona com payload mockado e payload real parcial;
- dado ausente aparece como ausente;
- sinais sao exploratorios ate backtesting.

### Fase 3 - Backtesting e metricas

Objetivo: separar sinal util de enfeite.

Codex:

- expandir `engine/backtest.py`;
- medir 1X2, gols, escanteios, forca comparativa e sinais do radar;
- implementar validacao walk-forward;
- comparar contra baseline simples.

Claude:

- criar visualizacao de metricas;
- explicar amostra, periodo, baseline e incerteza;
- criar tela de historico de sinais.

Gate:

- toda metrica exibida tem amostra e periodo;
- sem amostra suficiente, exibir status exploratorio;
- nenhuma acuracia sem baseline.

### Fase 4 - Fontes externas e dados reais

Objetivo: reduzir mock e alimentar camadas reais.

Codex:

- implementar ingestao e normalizacao;
- registrar fonte, timestamp e qualidade;
- implementar odds e movimento de mercado;
- criar ou revisar migrations;
- tratar falhas de fonte.

Claude:

- criar UI de status de fonte;
- explicar fonte parcial, indisponivel ou vencida;
- montar painel de auditoria visual.

Gate:

- cada fonte tem status;
- fonte indisponivel nao gera numero inventado;
- dados externos nao contaminam camadas proibidas.

### Fase 5 - Agregador real, banca e produto

Objetivo: evoluir de estrutura para decisao calibrada.

Codex:

- implementar stacking;
- implementar calibracao;
- calcular EV e Kelly apenas quando houver odds validas;
- implementar poda de camadas por coeficiente;
- adicionar testes de regressao.

Claude:

- criar experiencia final de consulta;
- apresentar divergencia modelo vs mercado;
- mostrar confianca e riscos;
- evitar promessa de lucro.

Gate:

- banca so aparece com probabilidade calibrada e odds validas;
- agregador informa modo ativo;
- cada recomendacao tem rastreabilidade.

## 10. Regras de validacao

Antes de merge:

- `git status` revisado;
- diffs revisados;
- testes relevantes rodados;
- contrato atualizado se output mudou;
- README ou docs atualizados se comportamento publico mudou;
- nenhum segredo ou artefato de build commitado.

Para `engine/`:

- rodar testes Python existentes;
- adicionar teste quando alterar formula ou output;
- preservar isolamento de camada.

Para `web/`:

- rodar build/lint quando dependencias estiverem disponiveis;
- validar estados de erro;
- nao depender de dados que o contrato nao fornece.

Para `db/`:

- migrations devem ser incrementais;
- nao reescrever migration ja aplicada sem decisao explicita;
- documentar impacto.

## 11. ADRs e revisao deste documento

Criar ADR quando a decisao:

- altera arquitetura de camadas;
- muda contrato engine/api/web;
- muda schema de banco;
- troca fonte de dados;
- altera regra de agregacao;
- muda estrategia de backtesting;
- cria custo recorrente relevante.

Local recomendado:

```text
docs/adr/YYYY-MM-DD-titulo-curto.md
```

Este documento deve ser revisto:

- ao final de cada fase;
- quando houver conflito recorrente;
- quando uma regra travar o projeto sem ganho real;
- quando uma premissa deixar de ser verdadeira.

## 12. Checklist rapido para novos trabalhos

Antes de iniciar:

- [ ] Estou na branch correta?
- [ ] Meu escopo esta escrito?
- [ ] Sei quais arquivos nao posso tocar?
- [ ] O outro agente depende desta saida?
- [ ] Ha contrato afetado?

Antes de finalizar:

- [ ] Testes relevantes rodaram?
- [ ] Docs foram atualizadas?
- [ ] Artefatos locais ficaram fora do commit?
- [ ] O PR explica risco e criterio de pronto?
- [ ] O revisor correto foi marcado?

## 13. Historico de revisoes

| Versao | Data | Mudanca |
|---|---|---|
| v0.1 | 2026-06-15 | Criacao do documento de governanca operacional |
| v0.2 | 2026-06-15 | Adicionado indice de coordenacao e handoff datado para Claude |
