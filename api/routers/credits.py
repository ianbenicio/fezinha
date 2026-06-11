"""Créditos: saldo, histórico de transações."""
from __future__ import annotations

from fastapi import APIRouter

from ..core import CurrentUser, UserDep, get_service_client

router = APIRouter(prefix="/credits", tags=["creditos"])


@router.get("")
async def get_saldo(user: CurrentUser = UserDep):
    sb = get_service_client()
    res = sb.table("credit_balance").select("saldo").eq("user_id", user.id).single().execute()
    return {"saldo": res.data["saldo"] if res.data else 0}


@router.get("/transactions")
async def get_transacoes(user: CurrentUser = UserDep, limit: int = 50):
    sb = get_service_client()
    res = (
        sb.table("credit_transactions")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"transacoes": res.data or []}
