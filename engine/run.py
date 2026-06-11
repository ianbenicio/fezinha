"""Orquestrador do motor Fezinha.

Versão atual: núcleo estatístico (Dixon-Coles) com força baseline.
Mesma assinatura/saída do engine_stub — substitui-o sem mudar o backend.

A medida que as camadas forem portadas (contexto, elenco, odds...), elas
ajustam os λ ANTES do Dixon-Coles e alimentam o agregador. Por ora, só o
núcleo estatístico produz probabilidade real.
"""
from __future__ import annotations

from typing import Any

from .dixon_coles import mercados_de_escanteios, mercados_de_gols
from .strength import estimar_lambdas


def analisar_partida(
    match: dict[str, Any],
    complexidade: str,
    mercados: list[str],
    perfil_risco: str,
) -> dict[str, Any]:
    casa_car = (match.get("mandante") or {}).get("caracteristicas")
    fora_car = (match.get("visitante") or {}).get("caracteristicas")

    lam = estimar_lambdas(casa_car, fora_car)
    gols = mercados_de_gols(lam.lh, lam.la)
    escanteios = mercados_de_escanteios(lam.escanteios)

    usando_baseline = casa_car is None or fora_car is None

    return {
        "_stub": False,
        "fonte": "nucleo_estatistico_dixon_coles",
        "baseline": usando_baseline,  # True = força default (ingestão pendente)
        "complexidade": complexidade,
        "mercados": mercados,
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
                "camadas_ativas": ["dixon_coles"],
                "camadas_pendentes": ["contexto", "elenco", "odds", "agregador_stacking"],
            },
        },
        "indice_confianca": {
            "valor": None,
            "leitura": "indisponivel_ate_agregador_completo",
        },
        "alertas": [
            {"tipo": "MOTOR_PARCIAL",
             "descricao": "Só núcleo estatístico ativo; sem contexto/odds/calibração."}
        ],
        "banca": {
            "perfil_em_uso": perfil_risco,
            "recomendacoes": [],
            "nota": "banca aguarda agregador calibrado + odds para calcular EV",
        },
    }


def _mais_provavel(g) -> str:
    pares = {"casa": g.prob_casa, "empate": g.prob_empate, "visitante": g.prob_visitante}
    return max(pares, key=pares.get)
