"""Sanity checks do núcleo Dixon-Coles. Rodar: python -m engine.test_dixon_coles"""
from __future__ import annotations

from .dixon_coles import mercados_de_escanteios, mercados_de_gols
from .strength import estimar_lambdas


def _aprox(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(a - b) <= tol


def test_1x2_soma_um():
    g = mercados_de_gols(1.5, 1.1)
    soma = g.prob_casa + g.prob_empate + g.prob_visitante
    assert _aprox(soma, 1.0), f"1X2 deve somar 1, deu {soma}"


def test_over_monotonico():
    g = mercados_de_gols(1.5, 1.1)
    o = g.over
    assert o["0.5"] > o["1.5"] > o["2.5"] > o["3.5"], "over deve decrescer com a linha"
    assert all(0 <= v <= 1 for v in o.values())


def test_mando_favorece_casa():
    # mesmo ataque, mas λ casa maior → casa mais provável que visitante
    g = mercados_de_gols(1.6, 0.9)
    assert g.prob_casa > g.prob_visitante


def test_simetria():
    a = mercados_de_gols(1.3, 1.3)
    assert _aprox(a.prob_casa, a.prob_visitante, 0.02), "λ iguais → casa≈visitante"


def test_escanteios_decresce():
    e = mercados_de_escanteios(9.5)
    assert e["8.5"] > e["9.5"] > e["10.5"]


def test_baseline_lambdas():
    lam = estimar_lambdas(None, None)
    assert 0.1 <= lam.lh <= 6.0 and 0.1 <= lam.la <= 6.0
    assert lam.lh > lam.la, "fator casa: λ casa > λ fora no baseline"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - falhas}/{len(fns)} passaram")
    raise SystemExit(1 if falhas else 0)
