"""Testes da Força Comparativa (rodar: python -m engine.test_forca_comparativa)."""
from __future__ import annotations

from .forca_comparativa import adversarios_comuns, calcular_ratings, comparar


def _jogo(h, a, gh, ga):
    return {"home_team_id": h, "away_team_id": a, "placar_casa": gh, "placar_fora": ga}


def test_transitividade():
    # A(1) venceu B(2); B venceu C(3) → A > B > C, mesmo sem A x C
    jogos = [_jogo(1, 2, 2, 0), _jogo(2, 3, 3, 1), _jogo(3, 1, 0, 1)]
    r = calcular_ratings(jogos)
    assert r[1].ifc > r[2].ifc > r[3].ifc, f"transitividade falhou: {r}"


def test_tudo_empate_ifc_50():
    jogos = [_jogo(1, 2, 1, 1), _jogo(2, 1, 0, 0), _jogo(1, 2, 2, 2)]
    r = calcular_ratings(jogos)
    assert abs(r[1].ifc - 50) <= 2 and abs(r[2].ifc - 50) <= 2, f"empates ≠ 50: {r}"


def test_ifc_range():
    jogos = [_jogo(1, 2, 5, 0), _jogo(1, 2, 4, 0), _jogo(2, 1, 0, 3)]
    r = calcular_ratings(jogos)
    for t in r.values():
        assert 0 <= t.ifc <= 100


def test_expectativa_favorece_mais_forte():
    jogos = [_jogo(1, 2, 3, 0), _jogo(2, 3, 0, 2), _jogo(1, 3, 4, 0), _jogo(3, 2, 1, 1)]
    c = comparar(jogos, 1, 2, {1: "A", 2: "B", 3: "C"})
    assert c is not None and c.expectativa_mandante > 0.5


def test_mando_desempata():
    # forças iguais → mando dá vantagem leve ao mandante
    jogos = [_jogo(1, 2, 1, 1), _jogo(2, 1, 1, 1)]
    c = comparar(jogos, 1, 2, {})
    assert c is not None and 0.5 < c.expectativa_mandante < 0.6


def test_adversarios_comuns():
    jogos = [_jogo(1, 3, 2, 0), _jogo(3, 2, 2, 0), _jogo(1, 2, 1, 1)]
    comuns = adversarios_comuns(jogos, 1, 2, {3: "C"})
    assert len(comuns) == 1 and comuns[0]["adversario"] == "C"
    assert "venceu" in comuns[0]["resultado_mandante"]
    assert "perdeu" in comuns[0]["resultado_visitante"]


def test_grafo_insuficiente():
    assert comparar([], 1, 2, {}) is None


if __name__ == "__main__":
    import sys
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
    sys.exit(1 if falhas else 0)
