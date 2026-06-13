"""Orquestrador do motor Fezinha.

Versão atual: núcleo estatístico (Dixon-Coles) com força baseline.
Mesma assinatura/saída do engine_stub — substitui-o sem mudar o backend.

Emite um TRACE: log de cada camada com tópico, resumo, justificativa, fonte,
entrada e saída. Camadas ainda não portadas aparecem com status "pendente".
"""
from __future__ import annotations

from typing import Any

from .dixon_coles import mercados_de_escanteios, mercados_de_gols
from .forca_comparativa import comparar
from .strength import PRIOR_LIGA, estimar_lambdas


def _tem_forca(car: dict | None) -> bool:
    return bool(car) and ("ataque" in car or "defesa" in car)


def _pct(n: float) -> str:
    return f"{n * 100:.1f}%"


def analisar_partida(
    match: dict[str, Any],
    complexidade: str,
    mercados: list[str],
    perfil_risco: str,
    historico: list[dict[str, Any]] | None = None,
    nomes: dict[int, str] | None = None,
) -> dict[str, Any]:
    casa = match.get("mandante") or {}
    fora = match.get("visitante") or {}
    casa_car = casa.get("caracteristicas")
    fora_car = fora.get("caracteristicas")
    nome_casa = casa.get("nome", "Mandante")
    nome_fora = fora.get("nome", "Visitante")

    trace: list[dict[str, Any]] = []

    # ── perfil_liga ─────────────────────────────────────
    trace.append({
        "camada": "perfil_liga",
        "topico": "Prior da liga (calibração)",
        "status": "ok",
        "resumo": "Ponto de partida: médias do Brasileirão Série A.",
        "justificativa": "Cada liga tem ritmo próprio de gols e fator casa. "
                         "O modelo parte da média da liga antes de ajustar por time.",
        "fonte": "Prior estatístico da liga (histórico agregado de temporadas).",
        "entrada": {"liga": match.get("liga", "brasileirao_serie_a")},
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

    # ── camadas pendentes (com fonte planejada) ─────────
    pendentes = [
        ("elenco_impacto", "Escalação / impacto de jogadores",
         "Escalações oficiais dos clubes + métricas xG/xA (FBref) → VAEP."),
        ("contexto_competitivo", "Situação na tabela / motivação",
         "Tabela e regulamento da competição."),
        ("fatos_relevantes", "Fatos relevantes (notícias)",
         "Notícias verificáveis e comunicados oficiais dos clubes (72h)."),
        ("odds", "Probabilidade implícita do mercado",
         "Casas de apostas (Bet365, Pinnacle, Betano...)."),
        ("agregador", "Fusão calibrada (stacking)",
         "Combinação treinada das camadas contra resultados históricos."),
        ("banca", "Recomendação de aposta (EV + Kelly)",
         "Cruzamento prob. do modelo × odds do mercado."),
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

    return {
        "_stub": False,
        "fonte": "nucleo_estatistico_dixon_coles",
        "baseline": not forca_real,
        "complexidade": complexidade,
        "mercados": mercados,
        "partida": {"mandante": nome_casa, "visitante": nome_fora},
        "lambdas": {"casa": lam.lh, "fora": lam.la, "escanteios": lam.escanteios},
        "agregador": {
            "resultado": {
                "prob_casa": gols.prob_casa,
                "prob_empate": gols.prob_empate,
                "prob_visitante": gols.prob_visitante,
                "resultado_mais_provavel": _mais_provavel(gols),
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
                "modo": "nucleo_apenas",
                "camadas_ativas": ["perfil_liga", "pi_ratings", "strength", "dixon_coles", "escanteios"],
                "camadas_pendentes": [p[0] for p in pendentes],
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
        "indice_confianca": {"valor": None, "leitura": "indisponivel_ate_agregador_completo"},
        "alertas": [{"tipo": "MOTOR_PARCIAL",
                     "descricao": "Só núcleo estatístico ativo; sem contexto/odds/calibração."}],
        "banca": {"perfil_em_uso": perfil_risco, "recomendacoes": [],
                  "nota": "banca aguarda agregador calibrado + odds para calcular EV"},
        "trace": trace,
    }


def _mais_provavel(g) -> str:
    pares = {"casa": g.prob_casa, "empate": g.prob_empate, "visitante": g.prob_visitante}
    return max(pares, key=pares.get)
