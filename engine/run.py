"""Orquestrador do motor Fezinha.

Versão atual: núcleo estatístico (Dixon-Coles) com força baseline.
Mesma assinatura/saída do engine_stub — substitui-o sem mudar o backend.

Emite um TRACE: log de cada camada com tópico, entrada e saída. As camadas
ainda não portadas aparecem com status "pendente", para o processo inteiro
ficar visível.
"""
from __future__ import annotations

from typing import Any

from .dixon_coles import mercados_de_escanteios, mercados_de_gols
from .strength import PRIOR_LIGA, estimar_lambdas


def _tem_forca(car: dict | None) -> bool:
    return bool(car) and ("ataque" in car or "defesa" in car)


def analisar_partida(
    match: dict[str, Any],
    complexidade: str,
    mercados: list[str],
    perfil_risco: str,
) -> dict[str, Any]:
    casa = match.get("mandante") or {}
    fora = match.get("visitante") or {}
    casa_car = casa.get("caracteristicas")
    fora_car = fora.get("caracteristicas")
    nome_casa = casa.get("nome", "Mandante")
    nome_fora = fora.get("nome", "Visitante")

    trace: list[dict[str, Any]] = []

    # ── Camada: perfil_liga (prior/calibração) ──────────
    trace.append({
        "camada": "perfil_liga",
        "topico": "Prior da liga (calibração)",
        "status": "ok",
        "entrada": {"liga": match.get("liga", "brasileirao_serie_a")},
        "saida": dict(PRIOR_LIGA),
    })

    # ── Camada: pi_ratings / força (núcleo) ─────────────
    forca_real = _tem_forca(casa_car) and _tem_forca(fora_car)
    trace.append({
        "camada": "pi_ratings",
        "topico": "Força dos times (ataque/defesa)",
        "status": "ok" if forca_real else "baseline",
        "entrada": {
            f"{nome_casa}": casa_car or "sem dados de força",
            f"{nome_fora}": fora_car or "sem dados de força",
        },
        "saida": "força real" if forca_real else "força default (1.0) — ingestão pendente",
    })

    # ── Camada: estimativa de λ ─────────────────────────
    lam = estimar_lambdas(casa_car, fora_car)
    trace.append({
        "camada": "strength",
        "topico": "Estimativa de gols esperados (λ)",
        "status": "ok",
        "entrada": {"prior": dict(PRIOR_LIGA), "forca_real": forca_real},
        "saida": {"lambda_casa": lam.lh, "lambda_fora": lam.la, "escanteios": lam.escanteios},
    })

    # ── Camada: Dixon-Coles (mercados de gols) ──────────
    gols = mercados_de_gols(lam.lh, lam.la)
    trace.append({
        "camada": "dixon_coles",
        "topico": "Matriz de placar → 1X2 / Over-Under / BTTS",
        "status": "ok",
        "entrada": {"lambda_casa": lam.lh, "lambda_fora": lam.la, "rho": -0.05},
        "saida": {
            "prob_casa": gols.prob_casa,
            "prob_empate": gols.prob_empate,
            "prob_visitante": gols.prob_visitante,
            "over_25": gols.over["2.5"],
            "btts": gols.btts_sim,
            "placar_provavel": gols.placar_provavel,
        },
    })

    # ── Camada: Poisson de escanteios ───────────────────
    escanteios = mercados_de_escanteios(lam.escanteios)
    trace.append({
        "camada": "escanteios",
        "topico": "Poisson de escanteios",
        "status": "ok",
        "entrada": {"total_esperado": lam.escanteios},
        "saida": escanteios,
    })

    # ── Camadas pendentes (ainda em YAML, não portadas) ─
    for nome, topico in [
        ("elenco_impacto", "Escalação / impacto de jogadores"),
        ("contexto_competitivo", "Situação na tabela / motivação"),
        ("odds", "Probabilidade implícita do mercado"),
        ("agregador", "Fusão calibrada (stacking)"),
        ("indice_confianca", "Quanto confiar na previsão"),
        ("banca", "Recomendação de aposta (EV + Kelly)"),
    ]:
        trace.append({
            "camada": nome,
            "topico": topico,
            "status": "pendente",
            "entrada": None,
            "saida": "camada ainda não implementada (roadmap)",
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
                "over_05": gols.over["0.5"],
                "over_15": gols.over["1.5"],
                "over_25": gols.over["2.5"],
                "over_35": gols.over["3.5"],
                "btts": gols.btts_sim,
            },
            "escanteios": {
                "over_85": escanteios["8.5"],
                "over_95": escanteios["9.5"],
                "over_105": escanteios["10.5"],
            },
            "meta": {
                "modo": "nucleo_apenas",
                "camadas_ativas": ["perfil_liga", "pi_ratings", "strength", "dixon_coles", "escanteios"],
                "camadas_pendentes": ["elenco_impacto", "contexto_competitivo", "odds", "agregador", "banca"],
            },
        },
        "indice_confianca": {"valor": None, "leitura": "indisponivel_ate_agregador_completo"},
        "alertas": [
            {"tipo": "MOTOR_PARCIAL",
             "descricao": "Só núcleo estatístico ativo; sem contexto/odds/calibração."}
        ],
        "banca": {"perfil_em_uso": perfil_risco, "recomendacoes": [],
                  "nota": "banca aguarda agregador calibrado + odds para calcular EV"},
        "trace": trace,
    }


def _mais_provavel(g) -> str:
    pares = {"casa": g.prob_casa, "empate": g.prob_empate, "visitante": g.prob_visitante}
    return max(pares, key=pares.get)
