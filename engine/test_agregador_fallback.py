"""Testes do agregador fallback.

Rodar: python -m engine.test_agregador_fallback
"""
from __future__ import annotations

from .agregador import agregar_odds_1x2
from .run import analisar_partida


def _jogo(h: int, a: int, gh: int, ga: int) -> dict:
    return {"home_team_id": h, "away_team_id": a, "placar_casa": gh, "placar_fora": ga}


def _match() -> dict:
    return {
        "liga": "brasileirao_serie_a",
        "home_team_id": 1,
        "away_team_id": 2,
        "mandante": {"id": 1, "nome": "Alfa SC", "caracteristicas": None},
        "visitante": {"id": 2, "nome": "Beta AC", "caracteristicas": None},
    }


def _historico() -> list[dict]:
    return [
        _jogo(1, 3, 3, 0),
        _jogo(3, 2, 2, 0),
        _jogo(1, 2, 1, 1),
        _jogo(1, 4, 2, 0),
        _jogo(4, 2, 1, 0),
    ]


def _odds_validas() -> list[dict]:
    return [
        {"mercado": "1x2", "selecao": "casa", "valor": 1.90, "casa_aposta": "Casa A"},
        {"mercado": "1x2", "selecao": "empate", "valor": 3.40, "casa_aposta": "Casa A"},
        {"mercado": "1x2", "selecao": "visitante", "valor": 4.20, "casa_aposta": "Casa A"},
        {"mercado": "1x2", "selecao": "casa", "valor": 1.95, "casa_aposta": "Casa B"},
        {"mercado": "1x2", "selecao": "empate", "valor": 3.30, "casa_aposta": "Casa B"},
        {"mercado": "1x2", "selecao": "visitante", "valor": 4.00, "casa_aposta": "Casa B"},
    ]


def _resultado(**kwargs) -> dict:
    return analisar_partida(
        match=_match(),
        complexidade="padrao",
        mercados=["1x2", "gols", "escanteios"],
        perfil_risco="moderado",
        historico=_historico(),
        nomes={1: "Alfa SC", 2: "Beta AC", 3: "Gama FC", 4: "Delta EC"},
        **kwargs,
    )


def _trace(r: dict, camada: str) -> dict:
    return next(t for t in r["trace"] if t["camada"] == camada)


def test_odds_remove_margem_com_duas_casas():
    odds = agregar_odds_1x2(_odds_validas())
    assert odds is not None
    assert odds.casas_validas == 2
    soma = odds.prob.casa + odds.prob.empate + odds.prob.visitante
    assert abs(soma - 1.0) <= 0.001
    assert odds.margem_media > 0


def test_odds_incompletas_nao_acionam_fallback():
    odds = agregar_odds_1x2(_odds_validas()[:3])
    assert odds is None


def test_modelo_only_funde_forca_sem_banca():
    r = _resultado()
    ag = r["agregador"]
    dixon = _trace(r, "dixon_coles")["saida"]

    assert ag["modo"] == "modelo_only"
    assert r["baseline"] is False
    assert ag["meta"]["pesos_modelo"]["forca_comparativa"] > 0
    assert ag["resultado"]["prob_casa"] != dixon["prob_casa"]
    assert r["banca"]["recomendacoes"] == []
    assert any(a["tipo"] == "SEM_ODDS" for a in r["alertas"])


def test_fallback_com_odds_validas_sem_ev_stake():
    r = _resultado(odds=_odds_validas())
    ag = r["agregador"]

    assert ag["modo"] == "fallback_pesos"
    assert ag["meta"]["pesos_em_uso"]["odds"] > 0
    assert _trace(r, "odds")["status"] == "ok"
    assert r["banca"]["recomendacoes"] == []
    assert "sem EV" in r["banca"]["nota"]
    assert any(a["tipo"] == "AGREGADOR_FALLBACK" for a in r["alertas"])


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
