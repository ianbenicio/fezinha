"""Fallback deterministico do agregador.

Este modulo e o unico ponto onde sinais independentes podem ser fundidos. Ele
nao calibra probabilidade por backtest e nao autoriza banca/EV.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PESOS_FALLBACK = {
    "modelo_proprio": 0.55,
    "odds": 0.30,
    "consenso": 0.15,
}

PESOS_MODELO_INTERNO = {
    "dixon_coles": 0.75,
    "forca_comparativa": 0.25,
}

SELECOES_1X2 = ("casa", "empate", "visitante")


@dataclass(frozen=True)
class Prob1X2:
    casa: float
    empate: float
    visitante: float

    def as_dict(self) -> dict[str, float]:
        return {
            "prob_casa": self.casa,
            "prob_empate": self.empate,
            "prob_visitante": self.visitante,
        }


@dataclass(frozen=True)
class OddsAgregadas:
    prob: Prob1X2
    casas_validas: int
    margem_media: float


def _clamp_prob(n: float) -> float:
    return max(0.0, min(1.0, n))


def _normalizar(p: Prob1X2) -> Prob1X2:
    vals = [_clamp_prob(p.casa), _clamp_prob(p.empate), _clamp_prob(p.visitante)]
    total = sum(vals)
    if total <= 0:
        return Prob1X2(0.0, 0.0, 0.0)
    return Prob1X2(*(round(v / total, 4) for v in vals))


def _misturar(fontes: list[tuple[str, Prob1X2, float]]) -> tuple[Prob1X2, dict[str, float]]:
    """Mistura fontes disponiveis e renormaliza pesos declarados."""
    peso_total = sum(peso for _, _, peso in fontes if peso > 0)
    if peso_total <= 0:
        return Prob1X2(0.0, 0.0, 0.0), {}

    pesos_em_uso: dict[str, float] = {}
    casa = empate = visitante = 0.0
    for nome, prob, peso in fontes:
        if peso <= 0:
            continue
        w = peso / peso_total
        pesos_em_uso[nome] = round(w, 4)
        casa += prob.casa * w
        empate += prob.empate * w
        visitante += prob.visitante * w
    return _normalizar(Prob1X2(casa, empate, visitante)), pesos_em_uso


def prob_modelo_dixon(gols: Any) -> Prob1X2:
    return _normalizar(Prob1X2(
        casa=float(gols.prob_casa),
        empate=float(gols.prob_empate),
        visitante=float(gols.prob_visitante),
    ))


def prob_forca_comparativa(comp: Any, empate_base: float) -> Prob1X2 | None:
    """Converte expectativa binaria da forca comparativa em 1X2.

    A camada de forca nao modela empate. Para nao inventar uma taxa de empate,
    preservamos o empate do Dixon-Coles e redistribuimos o restante pela
    expectativa do mandante.
    """
    if comp is None:
        return None
    p_casa_bin = getattr(comp, "expectativa_mandante", None)
    if p_casa_bin is None:
        return None
    empate = _clamp_prob(float(empate_base))
    restante = max(0.0, 1.0 - empate)
    casa = restante * _clamp_prob(float(p_casa_bin))
    visitante = restante - casa
    return _normalizar(Prob1X2(casa, empate, visitante))


def prob_modelo_proprio(gols: Any, comp: Any | None) -> tuple[Prob1X2, dict[str, float]]:
    dixon = prob_modelo_dixon(gols)
    prob_comp = prob_forca_comparativa(comp, dixon.empate)
    if prob_comp is None:
        return dixon, {"dixon_coles": 1.0}
    return _misturar([
        ("dixon_coles", dixon, PESOS_MODELO_INTERNO["dixon_coles"]),
        ("forca_comparativa", prob_comp, PESOS_MODELO_INTERNO["forca_comparativa"]),
    ])


def agregar_odds_1x2(odds: list[dict[str, Any]] | None, fonte_minima: int = 2) -> OddsAgregadas | None:
    """Remove margem e agrega odds 1X2 por casa.

    Espera linhas no formato da tabela `odds`: mercado, selecao, valor,
    casa_aposta. Odds incompletas ou com menos casas que `fonte_minima` nao
    acionam o fallback.
    """
    if not odds:
        return None

    por_casa: dict[str, dict[str, float]] = {}
    for row in odds:
        if row.get("mercado") != "1x2":
            continue
        selecao = str(row.get("selecao") or "").lower()
        if selecao not in SELECOES_1X2:
            continue
        try:
            valor = float(row.get("valor"))
        except (TypeError, ValueError):
            continue
        if valor <= 1.0:
            continue
        casa = str(row.get("casa_aposta") or "desconhecida")
        por_casa.setdefault(casa, {})[selecao] = valor

    probs: list[Prob1X2] = []
    margens: list[float] = []
    for selecoes in por_casa.values():
        if not all(k in selecoes for k in SELECOES_1X2):
            continue
        inv = {k: 1.0 / selecoes[k] for k in SELECOES_1X2}
        total = sum(inv.values())
        if total <= 0:
            continue
        margens.append(total - 1.0)
        probs.append(_normalizar(Prob1X2(
            casa=inv["casa"] / total,
            empate=inv["empate"] / total,
            visitante=inv["visitante"] / total,
        )))

    if len(probs) < fonte_minima:
        return None

    avg = Prob1X2(
        casa=sum(p.casa for p in probs) / len(probs),
        empate=sum(p.empate for p in probs) / len(probs),
        visitante=sum(p.visitante for p in probs) / len(probs),
    )
    return OddsAgregadas(
        prob=_normalizar(avg),
        casas_validas=len(probs),
        margem_media=round(sum(margens) / len(margens), 4),
    )


def agregar_fallback(
    *,
    gols: Any,
    comp: Any | None,
    forca_real: bool,
    odds: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Gera decisao do agregador v0 sem calibracao.

    Modos:
    - nucleo_apenas: so Dixon-Coles baseline.
    - modelo_only: modelo proprio tem algum sinal interno, mas sem odds validas.
    - fallback_pesos: modelo proprio + odds validas, com pesos fixos
      documentados e sem recomendacao de banca.
    """
    modelo, pesos_modelo = prob_modelo_proprio(gols, comp)
    odds_ag = agregar_odds_1x2(odds)

    tem_sinal_interno = forca_real or comp is not None
    if odds_ag is not None:
        prob_final, pesos_externos = _misturar([
            ("modelo_proprio", modelo, PESOS_FALLBACK["modelo_proprio"]),
            ("odds", odds_ag.prob, PESOS_FALLBACK["odds"]),
        ])
        modo = "fallback_pesos"
    else:
        prob_final = modelo
        pesos_externos = {"modelo_proprio": 1.0}
        modo = "modelo_only" if tem_sinal_interno else "nucleo_apenas"

    return {
        "modo": modo,
        "prob": prob_final,
        "pesos_modelo": pesos_modelo,
        "pesos_em_uso": pesos_externos,
        "odds": None if odds_ag is None else {
            "casas_validas": odds_ag.casas_validas,
            "margem_media": odds_ag.margem_media,
            "probabilidades": odds_ag.prob.as_dict(),
        },
        "calibrado": False,
    }


def resultado_mais_provavel(prob: Prob1X2) -> str:
    pares = {"casa": prob.casa, "empate": prob.empate, "visitante": prob.visitante}
    return max(pares, key=pares.get)
