"""Dixon-Coles — núcleo matemático do motor.

Recebe as taxas de gol esperadas (λ) de cada time e produz a matriz de placar,
da qual derivam TODOS os mercados de gols: 1X2, Over/Under, BTTS.

Referência: Dixon & Coles (1997). Correção tau (rho) ajusta a dependência
em placares baixos (0-0, 1-0, 0-1, 1-1) que o Poisson puro subestima.

Sem dependências externas (math puro) — matriz pequena, custo desprezível.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_GOLS = 10  # truncamento da matriz (P(>10 gols) ~ 0)


def _poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def _tau(i: int, j: int, lh: float, la: float, rho: float) -> float:
    """Correção Dixon-Coles para placares baixos."""
    if i == 0 and j == 0:
        return 1.0 - lh * la * rho
    if i == 0 and j == 1:
        return 1.0 + lh * rho
    if i == 1 and j == 0:
        return 1.0 + la * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def matriz_placar(lh: float, la: float, rho: float = -0.05) -> list[list[float]]:
    """Matriz P(i,j) normalizada (gols casa i × gols fora j)."""
    m = [[0.0] * (MAX_GOLS + 1) for _ in range(MAX_GOLS + 1)]
    total = 0.0
    for i in range(MAX_GOLS + 1):
        for j in range(MAX_GOLS + 1):
            p = _poisson(i, lh) * _poisson(j, la) * _tau(i, j, lh, la, rho)
            p = max(p, 0.0)
            m[i][j] = p
            total += p
    if total > 0:
        for i in range(MAX_GOLS + 1):
            for j in range(MAX_GOLS + 1):
                m[i][j] /= total
    return m


@dataclass
class MercadosGols:
    prob_casa: float
    prob_empate: float
    prob_visitante: float
    over: dict[str, float]      # {"0.5": .., "1.5": .., "2.5": .., "3.5": ..}
    btts_sim: float
    placar_provavel: str
    top3_placares: list[str]


def mercados_de_gols(lh: float, la: float, rho: float = -0.05) -> MercadosGols:
    m = matriz_placar(lh, la, rho)

    casa = empate = visitante = btts = 0.0
    linhas = {0.5: 0.0, 1.5: 0.0, 2.5: 0.0, 3.5: 0.0}
    placares: list[tuple[float, str]] = []

    for i in range(MAX_GOLS + 1):
        for j in range(MAX_GOLS + 1):
            p = m[i][j]
            if i > j:
                casa += p
            elif i == j:
                empate += p
            else:
                visitante += p
            if i >= 1 and j >= 1:
                btts += p
            for linha in linhas:
                if i + j > linha:
                    linhas[linha] += p
            placares.append((p, f"{i}x{j}"))

    placares.sort(reverse=True)
    return MercadosGols(
        prob_casa=round(casa, 4),
        prob_empate=round(empate, 4),
        prob_visitante=round(visitante, 4),
        over={str(k): round(v, 4) for k, v in linhas.items()},
        btts_sim=round(btts, 4),
        placar_provavel=placares[0][1],
        top3_placares=[p[1] for p in placares[:3]],
    )


def mercados_de_escanteios(total_esperado: float) -> dict[str, float]:
    """Poisson simples para escanteios (sem correção DC — não há empate relevante)."""
    linhas = [8.5, 9.5, 10.5]
    out: dict[str, float] = {}
    for linha in linhas:
        # P(total > linha) = 1 - P(total <= floor(linha))
        acum = sum(_poisson(k, total_esperado) for k in range(int(linha) + 1))
        out[str(linha)] = round(1.0 - acum, 4)
    return out
