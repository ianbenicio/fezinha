"""Consultas de partida — o produto core.

Fluxo: roda motor em preflight → bloqueia baseline → debita crédito → salva resultado.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import CurrentUser, UserDep, get_service_client
from ..pricing import COMPLEXIDADES, custo_de, plano_de
from engine import analisar_partida
from engine.run import motivo_resultado_nao_operacional, resultado_operacional

router = APIRouter(prefix="/queries", tags=["consultas"])


class NovaConsulta(BaseModel):
    match_id: int
    complexidade: str = "padrao"


@router.post("")
async def criar_consulta(payload: NovaConsulta, user: CurrentUser = UserDep):
    if payload.complexidade not in COMPLEXIDADES:
        raise HTTPException(400, f"complexidade inválida (use: {COMPLEXIDADES})")

    sb = get_service_client()
    plano = plano_de(payload.complexidade)
    custo = custo_de(payload.complexidade)

    # partida
    match = sb.table("matches").select("*").eq("id", payload.match_id).single().execute()
    if not match.data:
        raise HTTPException(404, "Partida não encontrada")

    # carrega força dos times (alimenta o λ do motor)
    dados_match = dict(match.data)
    ids = [dados_match["home_team_id"], dados_match["away_team_id"]]
    times = sb.table("teams").select("id, nome, caracteristicas").in_("id", ids).execute()
    by_id = {t["id"]: t for t in (times.data or [])}
    dados_match["mandante"] = by_id.get(dados_match["home_team_id"])
    dados_match["visitante"] = by_id.get(dados_match["away_team_id"])

    # histórico encerrado da liga (grafo da força comparativa) + nomes
    liga = dados_match.get("liga", "brasileirao_serie_a")
    hist = (
        sb.table("matches")
        .select("home_team_id, away_team_id, placar_casa, placar_fora")
        .eq("liga", liga).eq("status", "encerrado")
        .not_.is_("placar_casa", "null")
        .execute()
    )
    historico = hist.data or []
    todos_times = sb.table("teams").select("id, nome").eq("liga", liga).execute()
    nomes = {t["id"]: t["nome"] for t in (todos_times.data or [])}

    # odds manuais sao opcionais. Sem odds validas, o motor segue sem EV/banca.
    try:
        odds_res = (
            sb.table("odds")
            .select("mercado, selecao, valor, casa_aposta, capturado_em")
            .eq("match_id", payload.match_id)
            .execute()
        )
        odds = odds_res.data or []
    except Exception:
        odds = []

    # perfil de risco do usuário (alimenta a banca)
    perfil = (
        sb.table("profiles").select("perfil_risco").eq("id", user.id).single().execute()
    )
    perfil_risco = perfil.data["perfil_risco"] if perfil.data else "moderado"

    # Preflight antes do debito. Baseline puro nao e produto confiavel para consulta paga.
    try:
        resultado = analisar_partida(
            match=dados_match,
            complexidade=payload.complexidade,
            mercados=plano["mercados"],
            perfil_risco=perfil_risco,
            historico=historico,
            nomes=nomes,
            odds=odds,
        )
    except Exception:
        raise HTTPException(500, "Falha ao processar a analise; nenhum credito foi debitado")

    if not resultado_operacional(resultado):
        raise HTTPException(409, motivo_resultado_nao_operacional(resultado))

    # cria registro da consulta (status: processando)
    query = (
        sb.table("queries")
        .insert({
            "user_id": user.id,
            "match_id": payload.match_id,
            "complexidade": payload.complexidade,
            "custo_creditos": custo,
            "mercados": plano["mercados"],
            "status": "processando",
        })
        .execute()
    )
    query_id = query.data[0]["id"]

    # débito atômico
    debito = sb.rpc("consumir_creditos", {
        "p_user": user.id,
        "p_custo": custo,
        "p_motivo": f"consulta {payload.complexidade} #{query_id}",
        "p_query_id": query_id,
    }).execute()
    if not debito.data:
        sb.table("queries").update({"status": "erro"}).eq("id", query_id).execute()
        raise HTTPException(402, "Saldo de créditos insuficiente")

    sb.table("queries").update({
        "resultado": resultado, "status": "concluida",
    }).eq("id", query_id).execute()

    return {"query_id": query_id, "custo_creditos": custo, "resultado": resultado}


@router.get("")
async def historico(user: CurrentUser = UserDep, limit: int = 30):
    sb = get_service_client()
    res = (
        sb.table("queries")
        .select("id, match_id, complexidade, custo_creditos, mercados, status, created_at")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"consultas": res.data or []}


@router.get("/{query_id}")
async def detalhe(query_id: int, user: CurrentUser = UserDep):
    sb = get_service_client()
    res = (
        sb.table("queries").select("*").eq("id", query_id).eq("user_id", user.id)
        .single().execute()
    )
    if not res.data:
        raise HTTPException(404, "Consulta não encontrada")
    return res.data
