"""Força Comparativa — rating transitivo via grafo de resultados.

Implementa layers/forca_comparativa.yaml:
- Colley: resolve a cadeia transitiva (vitória vale mais contra quem vence muito).
- Massey: idem, ponderado por saldo de gols.
- IFC 0-100: nota única interpretável (50 = média da liga).
- Expectativa de confronto: logística sobre a diferença de IFC (família Elo).
- Adversários comuns: a cadeia A→B→C→D explicada com jogos reais.

Python puro (eliminação de Gauss) — sem numpy, leve pro Railway.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

MANDO_BONUS = 7.0      # pontos IFC equivalentes ao fator casa
ESCALA_LOGISTICA = 40.0  # divisor da logística (como Elo usa 400)


# ── álgebra: eliminação de Gauss com pivoteamento parcial ──
def _resolver(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("sistema singular")
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (m[i][n] - sum(m[i][j] * x[j] for j in range(i + 1, n))) / m[i][i]
    return x


@dataclass
class RatingTime:
    ifc: int
    colley: float
    massey: float
    leitura: str


@dataclass
class Comparativo:
    mandante: RatingTime
    visitante: RatingTime
    diferenca_ifc: int
    expectativa_mandante: float
    leitura: str
    adversarios_comuns: list[dict[str, str]] = field(default_factory=list)
    ajustes_aplicados: list[str] = field(default_factory=list)
    jogos_no_grafo: int = 0


def _leitura_ifc(ifc: float) -> str:
    if ifc >= 70: return "elite"
    if ifc >= 58: return "forte"
    if ifc >= 42: return "media"
    if ifc >= 30: return "fraca"
    return "critica"


def _leitura_comparativo(p_casa: float) -> str:
    if p_casa >= 0.70: return "vantagem_forte_casa"
    if p_casa >= 0.55: return "vantagem_casa"
    if p_casa > 0.45: return "equilibrio"
    if p_casa > 0.30: return "vantagem_fora"
    return "vantagem_forte_fora"


def calcular_ratings(jogos: list[dict[str, Any]]) -> dict[int, RatingTime]:
    """Colley + Massey sobre os jogos encerrados. Chave: team_id."""
    times = sorted({j["home_team_id"] for j in jogos} | {j["away_team_id"] for j in jogos})
    idx = {t: i for i, t in enumerate(times)}
    n = len(times)
    if n < 2:
        return {}

    # contadores
    nj = [0] * n
    vit = [0.0] * n          # vitórias (empate = 0.5)
    der = [0.0] * n
    saldo = [0.0] * n
    confrontos = [[0] * n for _ in range(n)]

    for j in jogos:
        h, a = idx[j["home_team_id"]], idx[j["away_team_id"]]
        gh, ga = j["placar_casa"], j["placar_fora"]
        nj[h] += 1; nj[a] += 1
        confrontos[h][a] += 1; confrontos[a][h] += 1
        saldo[h] += gh - ga; saldo[a] += ga - gh
        if gh > ga:   vit[h] += 1; der[a] += 1
        elif ga > gh: vit[a] += 1; der[h] += 1
        else:         vit[h] += 0.5; vit[a] += 0.5; der[h] += 0.5; der[a] += 0.5

    # Colley: (2+n_i)c_i - Σ_j n_ij c_j = 1 + (v_i - d_i)/2
    ac = [[(2 + nj[i]) if i == k else -confrontos[i][k] for k in range(n)] for i in range(n)]
    bc = [1 + (vit[i] - der[i]) / 2 for i in range(n)]
    colley = _resolver(ac, bc)

    # Massey: (n_i)r_i - Σ n_ij r_j = saldo_i ; última linha vira Σr=0
    am = [[nj[i] if i == k else -confrontos[i][k] for k in range(n)] for i in range(n)]
    bm = saldo[:]
    am[-1] = [1.0] * n
    bm[-1] = 0.0
    massey = _resolver(am, bm)

    out: dict[int, RatingTime] = {}
    for t, i in idx.items():
        ifc = 100 * (0.6 * colley[i] + 0.4 * (1 / (1 + math.exp(-massey[i] / 2))))
        ifc = max(0, min(100, ifc))
        out[t] = RatingTime(
            ifc=round(ifc),
            colley=round(colley[i], 4),
            massey=round(massey[i], 3),
            leitura=_leitura_ifc(ifc),
        )
    return out


def _descreve(gf: int, gs: int, em_casa: bool) -> str:
    local = "casa" if em_casa else "fora"
    if gf > gs: return f"venceu {gf}x{gs} ({local})"
    if gf < gs: return f"perdeu {gf}x{gs} ({local})"
    return f"empatou {gf}x{gs} ({local})"


def adversarios_comuns(
    jogos: list[dict[str, Any]],
    time_a: int,
    time_b: int,
    nomes: dict[int, str],
    max_itens: int = 4,
) -> list[dict[str, str]]:
    """A cadeia transitiva explicada: como A e B se saíram contra os mesmos rivais."""
    def jogos_de(t: int) -> dict[int, tuple[int, int, bool]]:
        res = {}
        for j in jogos:
            if j["home_team_id"] == t:
                res[j["away_team_id"]] = (j["placar_casa"], j["placar_fora"], True)
            elif j["away_team_id"] == t:
                res[j["home_team_id"]] = (j["placar_fora"], j["placar_casa"], False)
        return res

    ja, jb = jogos_de(time_a), jogos_de(time_b)
    comuns = [adv for adv in ja if adv in jb and adv not in (time_a, time_b)]

    # prioriza contraste (um venceu, outro não)
    def contraste(adv: int) -> int:
        ra = ja[adv][0] - ja[adv][1]
        rb = jb[adv][0] - jb[adv][1]
        return abs((ra > 0) - (rb > 0)) * 2 + abs((ra < 0) - (rb < 0))

    comuns.sort(key=contraste, reverse=True)
    return [
        {
            "adversario": nomes.get(adv, f"#{adv}"),
            "resultado_mandante": _descreve(*ja[adv]),
            "resultado_visitante": _descreve(*jb[adv]),
        }
        for adv in comuns[:max_itens]
    ]


def comparar(
    jogos: list[dict[str, Any]],
    mandante_id: int,
    visitante_id: int,
    nomes: dict[int, str],
    ajustes_externos: list[str] | None = None,
) -> Comparativo | None:
    """Comparativo completo do confronto. None se grafo insuficiente."""
    ratings = calcular_ratings(jogos)
    if mandante_id not in ratings or visitante_id not in ratings:
        return None
    rm, rv = ratings[mandante_id], ratings[visitante_id]

    diff = rm.ifc - rv.ifc
    p_casa = 1 / (1 + 10 ** (-(diff + MANDO_BONUS) / ESCALA_LOGISTICA))

    ajustes = [f"mando de campo (+{MANDO_BONUS:.0f} pts IFC)"]
    if ajustes_externos:
        ajustes.extend(ajustes_externos)

    return Comparativo(
        mandante=rm,
        visitante=rv,
        diferenca_ifc=diff,
        expectativa_mandante=round(p_casa, 4),
        leitura=_leitura_comparativo(p_casa),
        adversarios_comuns=adversarios_comuns(jogos, mandante_id, visitante_id, nomes),
        ajustes_aplicados=ajustes,
        jogos_no_grafo=len(jogos),
    )
