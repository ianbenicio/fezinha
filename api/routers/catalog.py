"""Catálogo: times, jogadores, partidas (Série A). Leitura autenticada."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core import CurrentUser, UserDep, get_service_client

router = APIRouter(prefix="/catalog", tags=["catalogo"])


@router.get("/teams")
async def listar_times(_: CurrentUser = UserDep, liga: str = "brasileirao_serie_a"):
    sb = get_service_client()
    res = sb.table("teams").select("id, nome, slug, escudo_url, liga").eq("liga", liga).order("nome").execute()
    return {"times": res.data or []}


@router.get("/teams/{team_id}")
async def detalhe_time(team_id: int, _: CurrentUser = UserDep):
    sb = get_service_client()
    time = sb.table("teams").select("*").eq("id", team_id).single().execute()
    if not time.data:
        raise HTTPException(404, "Time não encontrado")
    jogadores = (
        sb.table("players").select("*").eq("team_id", team_id).order("nome").execute()
    )
    return {"time": time.data, "jogadores": jogadores.data or []}


@router.get("/matches")
async def listar_partidas(
    _: CurrentUser = UserDep,
    liga: str = "brasileirao_serie_a",
    status: str | None = None,
):
    sb = get_service_client()
    q = sb.table("matches").select("*").eq("liga", liga)
    if status:
        q = q.eq("status", status)
    res = q.order("data_hora").execute()
    return {"partidas": res.data or []}
