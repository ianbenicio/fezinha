"""Orquestrador do motor Fezinha.

Versão atual: núcleo estatístico (Dixon-Coles) com força baseline.
Mesma assinatura/saída do engine_stub — substitui-o sem mudar o backend.

Emite um TRACE: log de cada camada com tópico, resumo, justificativa, fonte,
entrada e saída. Camadas ainda não portadas aparecem com status "pendente".
"""
from __future__ import annotations

from typing import Any

from .agregador import agregar_fallback, resultado_mais_provavel
from .dixon_coles import mercados_de_escanteios, mercados_de_gols
from .forca_comparativa import comparar
from .strength import PRIOR_LIGA, estimar_lambdas

LIGA_LABELS = {
    "brasileirao_serie_a": "Brasileirao Serie A",
    "brasileirao_serie_b": "Brasileirao Serie B",
}


def _tem_forca(car: dict | None) -> bool:
    return bool(car) and ("ataque" in car or "defesa" in car)


def _pct(n: float) -> str:
    return f"{n * 100:.1f}%"


def resultado_operacional(resultado: dict[str, Any]) -> bool:
    """True quando o payload tem sinal real suficiente para consulta paga."""
    modo = (resultado.get("agregador") or {}).get("modo")
    return not bool(resultado.get("baseline")) and modo != "nucleo_apenas"


def motivo_resultado_nao_operacional(resultado: dict[str, Any]) -> str:
    modo = (resultado.get("agregador") or {}).get("modo") or "desconhecido"
    alertas = resultado.get("alertas") or []
    tipos = ", ".join(str(alerta.get("tipo")) for alerta in alertas if alerta.get("tipo"))
    detalhe = f" Alertas: {tipos}." if tipos else ""
    return (
        "Dados insuficientes para analise confiavel: motor em modo "
        f"{modo}, sem forca real/historico suficiente para diferenciar os times."
        f"{detalhe} Credito nao debitado."
    )


def analisar_partida(
    match: dict[str, Any],
    complexidade: str,
    mercados: list[str],
    perfil_risco: str,
    historico: list[dict[str, Any]] | None = None,
    nomes: dict[int, str] | None = None,
    odds: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    casa = match.get("mandante") or {}
    fora = match.get("visitante") or {}
    casa_car = casa.get("caracteristicas")
    fora_car = fora.get("caracteristicas")
    nome_casa = casa.get("nome", "Mandante")
    nome_fora = fora.get("nome", "Visitante")
    liga = match.get("liga", "brasileirao_serie_a")
    liga_label = LIGA_LABELS.get(str(liga), str(liga))

    trace: list[dict[str, Any]] = []

    # ── perfil_liga ─────────────────────────────────────
    trace.append({
        "camada": "perfil_liga",
        "topico": "Prior da liga (calibração)",
        "status": "baseline",
        "resumo": f"Ponto de partida temporario para {liga_label}; ainda nao calibrado por liga.",
        "justificativa": "Cada liga tem ritmo proprio de gols e fator casa. "
                         "Nesta fase, o prior e uma constante temporaria, nao uma media validada da liga.",
        "fonte": "Prior temporario do motor; substituir por calibracao via resultados oficiais.",
        "entrada": {"liga": liga},
        "saida": dict(PRIOR_LIGA),
    })

    # ── pi_ratings / força ──────────────────────────────
    forca_real = _tem_forca(casa_car) and _tem_forca(fora_car)
    trace.append({
        "camada": "pi_ratings",
        "topico": "Força dos times (ataque/defesa)",
        "status": "ok" if forca_real else "baseline",
        "resumo": "Força individual dos times aplicada." if forca_real
                  else "Força padrão — todos os times tratados como média da liga.",
        "justificativa": "Ratings de ataque/defesa diferenciam os times." if forca_real
                         else "Os dados de desempenho individual ainda não foram ingeridos; "
                              "por isso jogos diferentes resultam em números parecidos.",
        "fonte": "Desempenho histórico (pi-ratings)" if forca_real
                 else "— (ingestão de dados pendente)",
        "entrada": {nome_casa: casa_car or "sem força", nome_fora: fora_car or "sem força"},
        "saida": "força real" if forca_real else "força default (1.0)",
    })

    # ── strength (λ) ────────────────────────────────────
    lam = estimar_lambdas(casa_car, fora_car)
    trace.append({
        "camada": "strength",
        "topico": "Gols esperados (λ)",
        "status": "ok",
        "resumo": f"Gols esperados: {nome_casa} {lam.lh} × {nome_fora} {lam.la}.",
        "justificativa": "O mando eleva os gols esperados do time da casa "
                         "(fator casa embutido no prior).",
        "fonte": "Cálculo: prior da liga × força dos times.",
        "entrada": {"prior_casa": PRIOR_LIGA["media_gols_casa"],
                    "prior_fora": PRIOR_LIGA["media_gols_fora"], "forca_real": forca_real},
        "saida": {"lambda_casa": lam.lh, "lambda_fora": lam.la, "escanteios": lam.escanteios},
    })

    # ── dixon_coles (gols) ──────────────────────────────
    gols = mercados_de_gols(lam.lh, lam.la)
    trace.append({
        "camada": "dixon_coles",
        "topico": "Matriz de placar → 1X2 / Over-Under / BTTS",
        "status": "ok",
        "resumo": f"{nome_casa} {_pct(gols.prob_casa)}, empate {_pct(gols.prob_empate)}, "
                  f"{nome_fora} {_pct(gols.prob_visitante)}. Placar provável {gols.placar_provavel}.",
        "justificativa": "Distribui as probabilidades sobre todos os placares possíveis, "
                         "com correção (rho) que ajusta empates e placares baixos.",
        "fonte": "Modelo Dixon-Coles (1997).",
        "entrada": {"lambda_casa": lam.lh, "lambda_fora": lam.la, "rho": -0.05},
        "saida": {"prob_casa": gols.prob_casa, "prob_empate": gols.prob_empate,
                  "prob_visitante": gols.prob_visitante, "over_25": gols.over["2.5"],
                  "btts": gols.btts_sim, "placar_provavel": gols.placar_provavel},
    })

    # ── escanteios ──────────────────────────────────────
    escanteios = mercados_de_escanteios(lam.escanteios)
    trace.append({
        "camada": "escanteios",
        "topico": "Poisson de escanteios",
        "status": "ok",
        "resumo": f"Total esperado ≈ {lam.escanteios} escanteios. "
                  f"Mais de 9.5: {_pct(escanteios['9.5'])}.",
        "justificativa": "Escanteios seguem distribuição de Poisson sobre a média da liga.",
        "fonte": "Poisson — média de escanteios da liga.",
        "entrada": {"total_esperado": lam.escanteios},
        "saida": escanteios,
    })

    # ── forca_comparativa (rating transitivo Colley+Massey) ──
    comp = None
    if historico:
        hid = match.get("home_team_id") or casa.get("id")
        aid = match.get("away_team_id") or fora.get("id")
        if hid and aid:
            comp = comparar(historico, hid, aid, nomes or {})
    if comp:
        trace.append({
            "camada": "forca_comparativa",
            "topico": "Força comparativa (cadeia de resultados)",
            "status": "ok",
            "resumo": f"{nome_casa} IFC {comp.mandante.ifc} ({comp.mandante.leitura}) x "
                      f"{nome_fora} IFC {comp.visitante.ifc} ({comp.visitante.leitura}). "
                      f"Expectativa do mandante: {_pct(comp.expectativa_mandante)}.",
            "justificativa": "Resolve a cadeia transitiva de TODOS os resultados da liga "
                             "(se A venceu B e B venceu C, A ganha crédito sobre C). "
                             "Nota 0-100; 50 = média da liga. Inclui bônus de mando.",
            "fonte": f"Colley + Massey sobre {comp.jogos_no_grafo} jogos oficiais (CBF).",
            "entrada": {"jogos_no_grafo": comp.jogos_no_grafo,
                        "ajustes": comp.ajustes_aplicados},
            "saida": {"ifc_mandante": comp.mandante.ifc, "ifc_visitante": comp.visitante.ifc,
                      "diferenca": comp.diferenca_ifc,
                      "expectativa_mandante": comp.expectativa_mandante,
                      "leitura": comp.leitura},
        })
    else:
        trace.append({
            "camada": "forca_comparativa",
            "topico": "Força comparativa (cadeia de resultados)",
            "status": "pendente",
            "resumo": "Sem histórico suficiente da liga para montar o grafo.",
            "justificativa": "Precisa de jogos encerrados dos dois times na temporada.",
            "fonte": "Resultados oficiais da liga.",
            "entrada": None,
            "saida": None,
        })

    # --- agregador fallback ---
    # fallback do agregador: unico ponto de fusao entre camadas independentes
    ag_decisao = agregar_fallback(gols=gols, comp=comp, forca_real=forca_real, odds=odds)
    ag_prob = ag_decisao["prob"]
    odds_info = ag_decisao["odds"]

    if odds_info:
        trace.append({
            "camada": "odds",
            "topico": "Probabilidade implicita do mercado",
            "status": "ok",
            "resumo": f"Odds 1X2 validas em {odds_info['casas_validas']} casas; margem media removida.",
            "justificativa": "Odds foram convertidas para probabilidades implicitas e normalizadas sem margem.",
            "fonte": "Tabela odds (entrada manual/aprovada).",
            "entrada": {"linhas_recebidas": len(odds or [])},
            "saida": odds_info,
            "qualidade": 3,
        })
    else:
        trace.append({
            "camada": "odds",
            "topico": "Probabilidade implicita do mercado",
            "status": "dado_ausente",
            "resumo": "Sem odds 1X2 validas com fonte minima.",
            "justificativa": "O fallback nao usa odds incompletas ou com menos de duas casas validas.",
            "fonte": "Tabela odds.",
            "entrada": {"linhas_recebidas": len(odds or [])},
            "saida": None,
            "qualidade": 0,
        })

    trace.append({
        "camada": "agregador",
        "topico": "Fusao fallback",
        "status": "ok",
        "resumo": f"Modo ativo: {ag_decisao['modo']}. Probabilidade ainda nao calibrada por backtest.",
        "justificativa": "A fusao acontece somente no agregador. Pesos fixos sao documentados e temporarios.",
        "fonte": "layers/agregador.yaml + engine/agregador.py",
        "entrada": {
            "dixon_coles": {"prob_casa": gols.prob_casa, "prob_empate": gols.prob_empate,
                            "prob_visitante": gols.prob_visitante},
            "forca_comparativa": None if not comp else {"expectativa_mandante": comp.expectativa_mandante},
            "odds": odds_info,
        },
        "saida": {
            "modo": ag_decisao["modo"],
            "prob_casa": ag_prob.casa,
            "prob_empate": ag_prob.empate,
            "prob_visitante": ag_prob.visitante,
            "pesos_modelo": ag_decisao["pesos_modelo"],
            "pesos_em_uso": ag_decisao["pesos_em_uso"],
            "calibrado": False,
        },
        "qualidade": 2 if ag_decisao["modo"] == "fallback_pesos" else 1,
    })

    trace.append({
        "camada": "banca",
        "topico": "EV + Kelly",
        "status": "pendente",
        "resumo": "Sem recomendacao de banca nesta fase.",
        "justificativa": "Banca exige probabilidade calibrada e odds validas; fallback nao basta para stake.",
        "fonte": "layers/banca.yaml",
        "entrada": {"modo_agregador": ag_decisao["modo"], "calibrado": False},
        "saida": {"recomendacoes": []},
        "qualidade": 0,
    })

    # --- camadas pendentes (com fonte planejada) ---
    pendentes = [
        ("elenco_impacto", "Escalação / impacto de jogadores",
         "Escalações oficiais dos clubes + métricas xG/xA (FBref) → VAEP."),
        ("contexto_competitivo", "Situação na tabela / motivação",
         "Tabela e regulamento da competição."),
        ("fatos_relevantes", "Fatos relevantes (notícias)",
         "Notícias verificáveis e comunicados oficiais dos clubes (72h)."),
    ]
    for nome, topico, fonte in pendentes:
        trace.append({
            "camada": nome,
            "topico": topico,
            "status": "pendente",
            "resumo": "Camada ainda não implementada.",
            "justificativa": "No roadmap — entra com a ingestão de dados e próximas fases.",
            "fonte": fonte,
            "entrada": None,
            "saida": None,
        })

    camadas_ativas = ["perfil_liga", "pi_ratings", "strength", "dixon_coles", "escanteios", "agregador"]
    if comp:
        camadas_ativas.append("forca_comparativa")
    if odds_info:
        camadas_ativas.append("odds")

    camadas_pendentes = [p[0] for p in pendentes]
    if not comp:
        camadas_pendentes.append("forca_comparativa")
    if not odds_info:
        camadas_pendentes.append("odds")
    camadas_pendentes.append("banca")

    alertas = []
    if ag_decisao["modo"] == "nucleo_apenas":
        alertas.append({
            "tipo": "MOTOR_PARCIAL",
            "descricao": "So nucleo estatistico ativo; sem forca comparativa, odds ou calibracao.",
            "severidade": "aviso",
        })
    elif ag_decisao["modo"] == "modelo_only":
        alertas.append({
            "tipo": "SEM_ODDS",
            "descricao": "Modelo proprio ativo, mas sem odds validas: sem EV/banca.",
            "severidade": "aviso",
        })
    else:
        alertas.append({
            "tipo": "AGREGADOR_FALLBACK",
            "descricao": "Fusao por pesos fixos ativa, ainda sem stacking/calibracao treinada.",
            "severidade": "aviso",
        })
    alertas.append({
        "tipo": "BANCA_INDISPONIVEL",
        "descricao": "Sem probabilidade calibrada: nenhuma recomendacao de stake ou EV e gerada.",
        "severidade": "info",
    })

    banca_nota = (
        "sem odds validas: sem EV/banca"
        if not odds_info
        else "fallback sem calibracao: sem EV/stake automatico"
    )

    return {
        "_stub": False,
        "fonte": "nucleo_estatistico_dixon_coles",
        "baseline": not (forca_real or comp),
        "complexidade": complexidade,
        "mercados": mercados,
        "partida": {"mandante": nome_casa, "visitante": nome_fora},
        "lambdas": {"casa": lam.lh, "fora": lam.la, "escanteios": lam.escanteios},
        "agregador": {
            "modo": ag_decisao["modo"],
            "resultado": {
                "prob_casa": ag_prob.casa,
                "prob_empate": ag_prob.empate,
                "prob_visitante": ag_prob.visitante,
                "resultado_mais_provavel": resultado_mais_provavel(ag_prob),
                "placar_provavel": gols.placar_provavel,
                "top3_placares": gols.top3_placares,
            },
            "gols": {
                "over_05": gols.over["0.5"], "over_15": gols.over["1.5"],
                "over_25": gols.over["2.5"], "over_35": gols.over["3.5"],
                "btts": gols.btts_sim,
            },
            "escanteios": {
                "over_85": escanteios["8.5"], "over_95": escanteios["9.5"],
                "over_105": escanteios["10.5"],
            },
            "meta": {
                "modo": ag_decisao["modo"],
                "camadas_ativas": camadas_ativas,
                "camadas_pendentes": camadas_pendentes,
                "pesos_em_uso": ag_decisao["pesos_em_uso"],
                "pesos_modelo": ag_decisao["pesos_modelo"],
                "calibrado": False,
                "data_ultimo_treino": None,
            },
        },
        "forca_comparativa": None if not comp else {
            "mandante": {"ifc": comp.mandante.ifc, "leitura": comp.mandante.leitura},
            "visitante": {"ifc": comp.visitante.ifc, "leitura": comp.visitante.leitura},
            "diferenca_ifc": comp.diferenca_ifc,
            "expectativa_mandante": comp.expectativa_mandante,
            "leitura": comp.leitura,
            "adversarios_comuns": comp.adversarios_comuns,
            "ajustes_aplicados": comp.ajustes_aplicados,
            "jogos_no_grafo": comp.jogos_no_grafo,
        },
        "indice_confianca": {"valor": None, "leitura": "indisponivel_ate_backtest_calibrado"},
        "alertas": alertas,
        "banca": {"perfil_em_uso": perfil_risco, "recomendacoes": [],
                  "nota": banca_nota},
        "trace": trace,
    }


def _mais_provavel(g) -> str:
    pares = {"casa": g.prob_casa, "empate": g.prob_empate, "visitante": g.prob_visitante}
    return max(pares, key=pares.get)
