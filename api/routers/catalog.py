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


@router.get("/news")
async def listar_noticias(_: CurrentUser = UserDep, liga: str | None = None, limit: int = 20):
    sb = get_service_client()
    q = sb.table("news").select("titulo, url, fonte, liga, imagem_url, publicado_em")
    if liga:
        q = q.eq("liga", liga)
    res = q.order("publicado_em", desc=True).limit(limit).execute()
    return {"noticias": res.data or []}


@router.get("/matches/{match_id}")
async def detalhe_partida(match_id: int, _: CurrentUser = UserDep):
    sb = get_service_client()
    m = sb.table("matches").select("*").eq("id", match_id).single().execute()
    if not m.data:
        raise HTTPException(404, "Partida não encontrada")
    partida = dict(m.data)
    ids = [partida["home_team_id"], partida["away_team_id"]]
    times = sb.table("teams").select("id, nome, slug, escudo_url, caracteristicas").in_("id", ids).execute()
    by_id = {t["id"]: t for t in (times.data or [])}
    partida["mandante"] = by_id.get(partida["home_team_id"])
    partida["visitante"] = by_id.get(partida["away_team_id"])
    # local aproximado: cidade do mandante (sem estádio no schema ainda)
    mand = partida["mandante"] or {}
    car = mand.get("caracteristicas") or {}
    partida["local"] = f'{car.get("cidade", "?")}/{car.get("estado", "")}'.strip("/")
    return {"partida": partida}


@router.get("/matches")
async def listar_partidas(
    _: CurrentUser = UserDep,
    liga: str | None = None,        # None = todas as ligas (para agrupar por campeonato)
    status: str | None = None,
):
    sb = get_service_client()
    q = sb.table("matches").select("*")
    if liga:
        q = q.eq("liga", liga)
    if status:
        q = q.eq("status", status)
    res = q.order("data_hora").execute()
    partidas = res.data or []

    # enriquece com nomes dos times (lookup único, todas as ligas)
    times = sb.table("teams").select("id, nome, slug, escudo_url").execute()
    by_id = {t["id"]: t for t in (times.data or [])}
    for p in partidas:
        p["mandante"] = by_id.get(p["home_team_id"])
        p["visitante"] = by_id.get(p["away_team_id"])

    return {"partidas": partidas}
