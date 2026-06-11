"""Custo de crédito por complexidade de consulta.

Tabela configurável. Reflete o custo real de inferência (mais camadas LLM +
mais mercados = mais caro). Margem embutida sobre o custo de LLM.
"""
from __future__ import annotations

# complexidade -> (custo_creditos, mercados_incluidos, camadas_llm)
PRICING: dict[str, dict] = {
    "simples": {
        "custo_creditos": 1,
        "mercados": ["1x2"],
        "camadas_llm": [],  # só fórmula
        "descricao": "1X2, núcleo estatístico + odds. Sem análise LLM.",
    },
    "padrao": {
        "custo_creditos": 3,
        "mercados": ["1x2", "over_under_gols", "escanteios"],
        "camadas_llm": ["fatos_relevantes", "visao_time", "elenco_impacto"],
        "descricao": "Todos os mercados + camadas contextuais LLM.",
    },
    "premium": {
        "custo_creditos": 5,
        "mercados": ["1x2", "over_under_gols", "escanteios"],
        "camadas_llm": [
            "fatos_relevantes", "visao_time", "elenco_impacto",
            "tatica_matchup", "visao_casas", "contexto_competitivo",
        ],
        "descricao": "Análise completa + múltiplas + relatório narrativo.",
    },
}

COMPLEXIDADES = tuple(PRICING.keys())


def custo_de(complexidade: str) -> int:
    if complexidade not in PRICING:
        raise ValueError(f"complexidade inválida: {complexidade}")
    return PRICING[complexidade]["custo_creditos"]


def plano_de(complexidade: str) -> dict:
    if complexidade not in PRICING:
        raise ValueError(f"complexidade inválida: {complexidade}")
    return PRICING[complexidade]
