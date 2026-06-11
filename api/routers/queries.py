"""Consultas de partida — o produto core.

Fluxo: valida saldo → debita crédito (atômico) → roda motor → salva resultado.
Se o motor falhar após o débito, estorna.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import CurrentUser, UserDep, get_service_client
from ..pricing import COMPLEXIDADES, custo_de, plano_de
from engine import analisar_partida

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

    # perfil de risco do usuário (alimenta a banca)
    perfil = (
        sb.table("profiles").select("perfil_risco").eq("id", user.id).single().execute()
    )
    perfil_risco = perfil.data["perfil_risco"] if perfil.data else "moderado"

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

    # roda o motor (stub por ora)
    try:
        resultado = analisar_partida(
            match=dados_match,
            complexidade=payload.complexidade,
            mercados=plano["mercados"],
            perfil_risco=perfil_risco,
        )
    except Exception:
        # estorna: custo negativo credita de volta e registra a transação (uma só).
        sb.rpc("estornar_creditos", {
            "p_user": user.id, "p_valor": custo,
            "p_motivo": f"estorno consulta #{query_id}", "p_query_id": query_id,
        }).execute()
        sb.table("queries").update({"status": "erro"}).eq("id", query_id).execute()
        raise HTTPException(500, "Falha ao processar a análise; crédito estornado")

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
