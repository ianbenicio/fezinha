"""Contrato engine -> api -> web v0.

Rodar: python -m engine.test_contract_v0
"""
from __future__ import annotations

from .run import analisar_partida, motivo_resultado_nao_operacional, resultado_operacional


MODOS_VALIDOS = {"nucleo_apenas", "modelo_only", "fallback_pesos"}
TRACE_STATUS_VALIDOS = {"ok", "baseline", "pendente", "dado_ausente", "fonte_vencida", "erro"}


def _match_baseline() -> dict:
    return {
        "liga": "brasileirao_serie_a",
        "home_team_id": 1,
        "away_team_id": 2,
        "mandante": {"id": 1, "nome": "Mandante FC", "caracteristicas": None},
        "visitante": {"id": 2, "nome": "Visitante EC", "caracteristicas": None},
    }


def _resultado() -> dict:
    return analisar_partida(
        match=_match_baseline(),
        complexidade="padrao",
        mercados=["1x2", "gols", "escanteios"],
        perfil_risco="moderado",
        historico=[],
        nomes={},
    )


def _assert_prob(n: object, nome: str) -> None:
    assert isinstance(n, (int, float)), f"{nome} deve ser numerico"
    assert 0 <= float(n) <= 1, f"{nome} deve estar entre 0 e 1"


def test_payload_tem_envelope_minimo():
    r = _resultado()
    for chave in [
        "_stub",
        "fonte",
        "baseline",
        "complexidade",
        "mercados",
        "partida",
        "lambdas",
        "agregador",
        "forca_comparativa",
        "indice_confianca",
        "alertas",
        "banca",
        "trace",
    ]:
        assert chave in r, f"campo obrigatorio ausente: {chave}"


def test_agregador_retrocompativel():
    ag = _resultado()["agregador"]

    resultado = ag["resultado"]
    for chave in ["prob_casa", "prob_empate", "prob_visitante", "resultado_mais_provavel", "placar_provavel"]:
        assert chave in resultado, f"agregador.resultado.{chave} ausente"
    _assert_prob(resultado["prob_casa"], "prob_casa")
    _assert_prob(resultado["prob_empate"], "prob_empate")
    _assert_prob(resultado["prob_visitante"], "prob_visitante")
    assert abs(resultado["prob_casa"] + resultado["prob_empate"] + resultado["prob_visitante"] - 1.0) <= 0.02

    gols = ag["gols"]
    for chave in ["over_15", "over_25", "over_35", "btts"]:
        assert chave in gols, f"agregador.gols.{chave} ausente"
        _assert_prob(gols[chave], chave)

    escanteios = ag["escanteios"]
    for chave in ["over_85", "over_95", "over_105"]:
        assert chave in escanteios, f"agregador.escanteios.{chave} ausente"
        _assert_prob(escanteios[chave], chave)


def test_modo_canonico_em_meta():
    ag = _resultado()["agregador"]
    meta = ag["meta"]
    assert ag["modo"] in MODOS_VALIDOS
    assert meta["modo"] in MODOS_VALIDOS
    assert ag["modo"] == meta["modo"]
    assert meta["modo"] == "nucleo_apenas"
    assert isinstance(meta["camadas_ativas"], list) and meta["camadas_ativas"]
    assert isinstance(meta["camadas_pendentes"], list)


def test_confianca_alertas_banca_formalizados():
    r = _resultado()

    conf = r["indice_confianca"]
    assert set(conf) >= {"valor", "leitura"}
    assert conf["valor"] is None or 0 <= conf["valor"] <= 1
    assert isinstance(conf["leitura"], str) and conf["leitura"]

    assert isinstance(r["alertas"], list)
    for alerta in r["alertas"]:
        assert isinstance(alerta.get("tipo"), str) and alerta["tipo"]
        assert isinstance(alerta.get("descricao"), str) and alerta["descricao"]

    banca = r["banca"]
    assert isinstance(banca.get("perfil_em_uso"), str) and banca["perfil_em_uso"]
    assert isinstance(banca.get("recomendacoes"), list)
    assert banca["recomendacoes"] == [], "sem odds validas nao deve haver recomendacao"
    assert isinstance(banca.get("nota"), str) and banca["nota"]


def test_trace_tem_status_e_qualidade_valida_quando_presente():
    trace = _resultado()["trace"]
    assert isinstance(trace, list) and trace

    for item in trace:
        for chave in ["camada", "topico", "status", "entrada", "saida"]:
            assert chave in item, f"trace item sem {chave}: {item}"
        assert item["status"] in TRACE_STATUS_VALIDOS
        if "qualidade" in item:
            assert isinstance(item["qualidade"], (int, float))
            assert 0 <= item["qualidade"] <= 5


def test_forca_comparativa_explicativa_ou_nula():
    r = _resultado()
    assert r["forca_comparativa"] is None


def test_baseline_nao_e_operacional_para_consulta_paga():
    r = _resultado()
    assert r["baseline"] is True
    assert resultado_operacional(r) is False
    assert "Credito nao debitado" in motivo_resultado_nao_operacional(r)


def test_modelo_com_historico_e_operacional():
    r = analisar_partida(
        match={
            "liga": "brasileirao_serie_a",
            "home_team_id": 1,
            "away_team_id": 2,
            "mandante": {"id": 1, "nome": "Mandante FC", "caracteristicas": None},
            "visitante": {"id": 2, "nome": "Visitante EC", "caracteristicas": None},
        },
        complexidade="padrao",
        mercados=["1x2", "gols", "escanteios"],
        perfil_risco="moderado",
        historico=[
            {"home_team_id": 1, "away_team_id": 3, "placar_casa": 2, "placar_fora": 0},
            {"home_team_id": 3, "away_team_id": 2, "placar_casa": 1, "placar_fora": 0},
            {"home_team_id": 1, "away_team_id": 2, "placar_casa": 1, "placar_fora": 1},
        ],
        nomes={1: "Mandante FC", 2: "Visitante EC", 3: "Terceiro FC"},
    )
    assert r["baseline"] is False
    assert resultado_operacional(r) is True


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
