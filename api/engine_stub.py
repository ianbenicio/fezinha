"""Stub do motor Fezinha.

Placeholder até as 24 camadas (engine/) serem implementadas em Python.
Retorna a MESMA estrutura que o agregador final produzirá, com valores
mockados, para que a plataforma rode ponta-a-ponta desde já.

Contrato de saída espelha agregador.yaml + banca.yaml.
"""
from __future__ import annotations

from typing import Any


def analisar_partida(
    match: dict[str, Any],
    complexidade: str,
    mercados: list[str],
    perfil_risco: str,
) -> dict[str, Any]:
    """Retorna análise mockada no formato do agregador + banca.

    TODO: substituir pela chamada real ao motor (engine/) quando as
    camadas estiverem implementadas. A interface (assinatura + formato de
    retorno) é estável — só o miolo muda.
    """
    resultado: dict[str, Any] = {
        "_stub": True,
        "partida": match,
        "complexidade": complexidade,
        "mercados": mercados,
        "agregador": {
            "resultado": {
                "prob_casa": 0.0,
                "prob_empate": 0.0,
                "prob_visitante": 0.0,
                "resultado_mais_provavel": None,
            },
            "gols": {"over_15": 0.0, "over_25": 0.0, "over_35": 0.0, "btts": 0.0},
            "escanteios": {"over_85": 0.0, "over_95": 0.0, "over_105": 0.0},
            "meta": {"modo": "stub", "camadas_ativas": [], "camadas_podadas": []},
        },
        "indice_confianca": {"valor": 0.0, "leitura": "indisponivel"},
        "alertas": [],
        "banca": {
            "perfil_em_uso": perfil_risco,
            "recomendacoes": [],
            "exposicao_rodada": 0.0,
        },
    }
    return resultado
