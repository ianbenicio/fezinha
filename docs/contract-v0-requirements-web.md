# Requisitos do contract-v0 — lado consumidor (web)

> **Insumo para a Fase 1A (Codex desenha o contrato `engine → api → web`).**
> Isto **não é** o contrato — é a lista do que o web precisa que o contrato contenha,
> derivada da revisão do motor + do mapa de consumo atual (`docs/web-map.md`).
> Revisor produtor: Codex. Revisor consumidor: Claude.

## Regras inegociáveis (senão `/consulta` quebra ou a UI mente)

1. **Retrocompatibilidade.** O `/consulta/[matchId]` já lê em produção o bloco
   `Resultado.agregador` com estes campos — **não renomear**:
   ```
   agregador.resultado: prob_casa, prob_empate, prob_visitante,
                        resultado_mais_provavel, placar_provavel
   agregador.gols:      over_15, over_25, over_35, btts
   agregador.escanteios: over_85, over_95, over_105
   ```
   Adicionar campos é seguro; renomear/remover é breaking.

2. **Campo `agregador.modo`** (enum). Hoje o `run.py:211` emite `"modo": "nucleo_apenas"`
   dentro de `agregador.meta`, e há só o bool `baseline` no topo — **insuficiente** para a UI
   distinguir os estados. Formalizar o enum, reusando o valor já existente:
   ```
   modo: "nucleo_apenas" | "modelo_only" | "fallback_pesos"
   ```
   (usar `nucleo_apenas`, não `nucleo_only`, p/ casar com o código atual.)
   A UI mapeia: `nucleo_apenas` → "motor parcial (sem força individual)";
   `modelo_only` → "sem odds: sem EV/banca"; `fallback_pesos` → "fusão por pesos fixos".

3. **Formalizar `indice_confianca`, `alertas`, `banca`.** O `run.py` **já retorna os três**
   (`indice_confianca: {valor, leitura}`, `alertas: [{tipo, descricao}]`, `banca: {...}`),
   e o web **ignora hoje**. É folga: especificar o shape e o web passa a renderizar
   confiança/alertas/banca **sem breaking change**.
   - `banca`: deixar explícito quando **não há recomendação** (sem odds → sem EV).
     A UI mostra "sem recomendação de banca", nunca um EV inventado.

4. **Qualidade/status por camada no `trace`.** O `trace[]` já traz `status`
   (`ok` | `baseline` | `pendente`). Para os estados "camada pendente" / "dado ausente" /
   "fonte vencida", expor por item: `status`, e quando aplicável `qualidade` (0-5) e
   `fonte`/`fonte_ausente`. A UI não inventa dado: ausente aparece como ausente.

5. **Autoridade da `forca_comparativa` (decisão de contrato).**
   Hoje `/consulta` mostra **dois números de resultado que podem se contradizer**:
   a `expectativa_mandante` (IFC, via Colley/Massey) **e** o `prob_casa` (Dixon-Coles).
   Liga ao achado da revisão: força comparativa é **calculada mas nunca fundida**.
   O contrato precisa declarar **qual é a verdade exibida**:
   - opção A: `forca_comparativa` é **decorativa/explicativa** (a UI rotula como "leitura
     alternativa", não como a probabilidade); ou
   - opção B: ela é **fundida** no `agregador.resultado` (aí o IFC não aparece como prob
     concorrente, só como evidência).
   Sem essa decisão, a UI exibe contradição. Preferência do consumidor: **A agora**
   (decorativa, rotulada), **B quando o agregador real fundir** (Fase 1B/5).

## Campos que a UI consome (resumo, de `docs/web-map.md`)
- Catálogo: `Match`, `Partida`, `TeamRef {nome, escudo_url?}`, `Noticia`, `Consulta`.
- Previsão: `Resultado { partida?, baseline?, forca_comparativa?, agregador, trace[] }`.
- Endpoints: `GET /catalog/matches[?status]`, `GET /catalog/matches/{id}`,
  `GET /catalog/news`, `POST /queries`, `GET /queries`, `GET /credits`.

## Gate de aceite (do lado web)
- [ ] shape retrocompatível com o `Resultado.agregador` atual;
- [ ] `agregador.modo` presente com os 3 valores;
- [ ] `indice_confianca` / `alertas` / `banca` com shape definido;
- [ ] `trace` com `status` (+ `qualidade`/`fonte` quando aplicável);
- [ ] autoridade da `forca_comparativa` decidida e documentada;
- [ ] teste de shape do payload (lado Codex) cobrindo os campos acima.
