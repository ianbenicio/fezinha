"""Backtest do modelo contra resultados reais (seção 24).

Valida se o Dixon-Coles + força prevê melhor que baselines simples.
RIGOR ANTI-VAZAMENTO (walk-forward): cada rodada R é prevista usando força
calculada SÓ com as rodadas 1..R-1 — o modelo nunca vê o jogo que prevê.

Métricas:
- Acurácia 1X2 (% de acerto do resultado mais provável)
- Brier Score multiclasse (erro das probabilidades; menor = melhor)
- Comparação vs baselines: sempre-mandante, e favorito-por-força

Uso: python -m engine.backtest <caminho_pdf>
"""
from __future__ import annotations

import sys
from collections import defaultdict
from typing import Any

from .dixon_coles import mercados_de_gols
from .strength import PRIOR_LIGA


def _forca_ate(jogos: list[dict[str, Any]]) -> dict[int, dict[str, float]]:
    """Ataque/defesa relativos (1.0 = média) a partir de um conjunto de jogos."""
    gm = defaultdict(int); gs = defaultdict(int); nj = defaultdict(int)
    for j in jogos:
        h, a, gh, ga = j["home"], j["away"], j["gh"], j["ga"]
        gm[h] += gh; gs[h] += ga; nj[h] += 1
        gm[a] += ga; gs[a] += gh; nj[a] += 1
    if not nj:
        return {}
    media = sum(gm.values()) / sum(nj.values())
    return {
        t: {"ataque": (gm[t] / nj[t]) / media, "defesa": (gs[t] / nj[t]) / media}
        for t in nj
    }


def _prever(forca: dict, home: int, away: int) -> tuple[float, float, float]:
    fc = forca.get(home, {"ataque": 1.0, "defesa": 1.0})
    fv = forca.get(away, {"ataque": 1.0, "defesa": 1.0})
    lh = PRIOR_LIGA["media_gols_casa"] * fc["ataque"] * fv["defesa"]
    la = PRIOR_LIGA["media_gols_fora"] * fv["ataque"] * fc["defesa"]
    lh = min(max(lh, 0.1), 6.0); la = min(max(la, 0.1), 6.0)
    g = mercados_de_gols(lh, la)
    return g.prob_casa, g.prob_empate, g.prob_visitante


def _forca_casa_fora(jogos: list[dict[str, Any]]) -> dict:
    """Força SEPARADA casa/fora — captura o fator mando por time."""
    from collections import defaultdict
    gm_c = defaultdict(int); gs_c = defaultdict(int); nj_c = defaultdict(int)
    gm_f = defaultdict(int); gs_f = defaultdict(int); nj_f = defaultdict(int)
    for j in jogos:
        gm_c[j["home"]] += j["gh"]; gs_c[j["home"]] += j["ga"]; nj_c[j["home"]] += 1
        gm_f[j["away"]] += j["ga"]; gs_f[j["away"]] += j["gh"]; nj_f[j["away"]] += 1
    tot_c = sum(nj_c.values()) or 1
    media_c = sum(gm_c.values()) / tot_c          # média de gols do mandante
    media_f = sum(gm_f.values()) / tot_c          # média de gols do visitante
    out = {}
    times = set(nj_c) | set(nj_f)
    for t in times:
        out[t] = {
            "atq_casa": (gm_c[t] / nj_c[t] / media_c) if nj_c[t] else 1.0,
            "def_casa": (gs_c[t] / nj_c[t] / media_f) if nj_c[t] else 1.0,
            "atq_fora": (gm_f[t] / nj_f[t] / media_f) if nj_f[t] else 1.0,
            "def_fora": (gs_f[t] / nj_f[t] / media_c) if nj_f[t] else 1.0,
        }
    return {"forca": out, "media_c": media_c, "media_f": media_f}


def _prever_cf(modelo: dict, home: int, away: int) -> tuple[float, float, float]:
    f = modelo["forca"]
    fc = f.get(home, {"atq_casa": 1.0, "def_casa": 1.0})
    fv = f.get(away, {"atq_fora": 1.0, "def_fora": 1.0})
    lh = modelo["media_c"] * fc["atq_casa"] * fv["def_fora"]
    la = modelo["media_f"] * fv["atq_fora"] * fc["def_casa"]
    lh = min(max(lh, 0.1), 6.0); la = min(max(la, 0.1), 6.0)
    g = mercados_de_gols(lh, la)
    return g.prob_casa, g.prob_empate, g.prob_visitante


def _resultado(gh: int, ga: int) -> str:
    return "casa" if gh > ga else ("visitante" if ga > gh else "empate")


def backtest(jogos: list[dict[str, Any]], rodada_inicio: int = 6) -> dict[str, Any]:
    por_rodada = defaultdict(list)
    for j in jogos:
        por_rodada[j["rodada"]].append(j)
    rodadas = sorted(por_rodada)

    n = 0
    acertos_modelo = acertos_cf = acertos_mando = 0
    brier_modelo = brier_cf = brier_uniforme = 0.0
    brier_mando_acc = [0.0]
    idx = {"casa": 0, "empate": 1, "visitante": 2}

    for r in rodadas:
        if r < rodada_inicio:
            continue
        treino = [j for j in jogos if j["rodada"] < r]
        forca = _forca_ate(treino)
        modelo_cf = _forca_casa_fora(treino)
        for j in por_rodada[r]:
            real = _resultado(j["gh"], j["ga"]); n += 1
            alvo = [0, 0, 0]; alvo[idx[real]] = 1

            # modelo força única
            probs = list(_prever(forca, j["home"], j["away"]))
            if ["casa", "empate", "visitante"][probs.index(max(probs))] == real: acertos_modelo += 1
            brier_modelo += sum((probs[k] - alvo[k]) ** 2 for k in range(3))

            # modelo força casa/fora
            pcf = list(_prever_cf(modelo_cf, j["home"], j["away"]))
            if ["casa", "empate", "visitante"][pcf.index(max(pcf))] == real: acertos_cf += 1
            brier_cf += sum((pcf[k] - alvo[k]) ** 2 for k in range(3))

            # baseline
            if real == "casa": acertos_mando += 1
            brier_uniforme += sum((1/3 - alvo[k]) ** 2 for k in range(3))
            # Brier do "sempre mandante" = prob [1,0,0]
            brier_mando_acc[0] += sum(([1, 0, 0][k] - alvo[k]) ** 2 for k in range(3))

    return {
        "jogos_testados": n,
        "acuracia_modelo": round(acertos_modelo / n, 3) if n else 0,
        "acuracia_casa_fora": round(acertos_cf / n, 3) if n else 0,
        "acuracia_sempre_mandante": round(acertos_mando / n, 3) if n else 0,
        "brier_modelo": round(brier_modelo / n, 4) if n else 0,
        "brier_casa_fora": round(brier_cf / n, 4) if n else 0,
        "brier_sempre_mandante": round(brier_mando_acc[0] / n, 4) if n else 0,
        "brier_chute_uniforme": round(brier_uniforme / n, 4) if n else 0,
    }


def _carregar_pdf(caminho: str) -> list[dict[str, Any]]:
    from .ingestion.cbf_tabela import parse_pdf
    SID = {"athletico-pr":1,"atletico-mg":2,"bahia":3,"botafogo":4,"chapecoense":5,
           "corinthians":6,"coritiba":7,"cruzeiro":8,"flamengo":9,"fluminense":10,
           "gremio":11,"internacional":12,"mirassol":13,"palmeiras":14,"bragantino":15,
           "remo":16,"santos":17,"sao-paulo":18,"vasco":19,"vitoria":20}
    out = []
    for j in parse_pdf(caminho):
        if j.placar_casa is None:
            continue
        out.append({"rodada": j.rodada, "home": SID[j.casa_slug], "away": SID[j.fora_slug],
                    "gh": j.placar_casa, "ga": j.placar_fora})
    return out


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "_tabela.pdf"
    jogos = _carregar_pdf(caminho)
    res = backtest(jogos)
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"=== BACKTEST ({res['jogos_testados']} jogos, walk-forward) ===")
    print(f"Acuracia 1X2:")
    print(f"  forca unica (atual)      {res['acuracia_modelo']*100:.1f}%")
    print(f"  forca casa/fora (novo)   {res['acuracia_casa_fora']*100:.1f}%")
    print(f"  baseline sempre-mandante {res['acuracia_sempre_mandante']*100:.1f}%")
    print(f"Brier Score (menor=melhor) — qualidade da PROBABILIDADE:")
    print(f"  forca unica (modelo)     {res['brier_modelo']}")
    print(f"  sempre-mandante          {res['brier_sempre_mandante']}")
    print(f"  chute uniforme           {res['brier_chute_uniforme']}")
    bm = res['brier_modelo'] < res['brier_sempre_mandante']
    print(f"\nEm Brier (o que importa p/ aposta), modelo {'SUPERA' if bm else 'perde p/'} sempre-mandante.")
