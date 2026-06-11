"""Perfil do usuário autenticado."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core import CurrentUser, UserDep, get_service_client

router = APIRouter(prefix="/me", tags=["perfil"])


@router.get("")
async def get_me(user: CurrentUser = UserDep):
    """Perfil + saldo de créditos do usuário logado."""
    sb = get_service_client()
    perfil = sb.table("profiles").select("*").eq("id", user.id).single().execute()
    if not perfil.data:
        raise HTTPException(404, "Perfil não encontrado")
    saldo = (
        sb.table("credit_balance").select("saldo").eq("user_id", user.id).single().execute()
    )
    return {
        "perfil": perfil.data,
        "saldo": saldo.data["saldo"] if saldo.data else 0,
    }


@router.patch("")
async def update_me(payload: dict, user: CurrentUser = UserDep):
    """Atualiza perfil_risco e preferências."""
    permitido = {k: v for k, v in payload.items() if k in ("nome", "perfil_risco", "preferencias")}
    if not permitido:
        raise HTTPException(400, "Nada a atualizar")
    sb = get_service_client()
    res = sb.table("profiles").update(permitido).eq("id", user.id).execute()
    return {"perfil": res.data[0] if res.data else None}
