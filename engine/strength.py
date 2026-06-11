"""Estima as taxas de gol esperadas (λ) de cada time para a partida.

λ_casa = base_liga * ataque_casa * defesa_visitante
λ_fora = base_liga * ataque_visitante * defesa_casa

Força vem de `teams.caracteristicas` (jsonb) quando a ingestão a popula
(ataque/defesa relativos, 1.0 = média da liga). Sem dado, usa 1.0 (baseline).

Prior da liga (perfil_liga): médias do Brasileirão. Substituir por valores
calibrados quando houver histórico.
"""
from __future__ import annotations

from dataclasses import dataclass

# Prior Brasileirão Série A (baseline até a ingestão calibrar)
PRIOR_LIGA = {
    "media_gols_casa": 1.45,
    "media_gols_fora": 1.05,
    "media_escanteios": 9.5,
}


@dataclass
class Lambdas:
    lh: float       # gols esperados mandante
    la: float       # gols esperados visitante
    escanteios: float


def _forca(caracteristicas: dict | None, chave: str) -> float:
    if not caracteristicas:
        return 1.0
    val = caracteristicas.get(chave)
    return float(val) if isinstance(val, (int, float)) and val > 0 else 1.0


def estimar_lambdas(
    casa_caracteristicas: dict | None,
    fora_caracteristicas: dict | None,
    prior: dict | None = None,
) -> Lambdas:
    p = prior or PRIOR_LIGA

    atq_casa = _forca(casa_caracteristicas, "ataque")
    def_casa = _forca(casa_caracteristicas, "defesa")
    atq_fora = _forca(fora_caracteristicas, "ataque")
    def_fora = _forca(fora_caracteristicas, "defesa")

    lh = p["media_gols_casa"] * atq_casa * def_fora
    la = p["media_gols_fora"] * atq_fora * def_casa

    # cap defensivo contra valores degenerados
    lh = min(max(lh, 0.1), 6.0)
    la = min(max(la, 0.1), 6.0)

    return Lambdas(lh=round(lh, 3), la=round(la, 3), escanteios=p["media_escanteios"])
