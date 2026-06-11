"""Configuração central, clients Supabase e autenticação."""
from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import Client, create_client


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_publishable_key: str
    supabase_service_role_key: str
    anthropic_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@lru_cache
def get_service_client() -> Client:
    """Client com service_role — bypassa RLS. Uso restrito ao backend."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


class CurrentUser:
    def __init__(self, user_id: str, email: str | None):
        self.id = user_id
        self.email = email


async def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    """Valida o Bearer JWT emitido pelo Supabase Auth."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token ausente")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        # MVP: decodifica claims sem verificar assinatura.
        # TODO (pré-produção): validar assinatura via JWKS do Supabase.
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sem sub")
    return CurrentUser(user_id=user_id, email=payload.get("email"))


UserDep = Depends(get_current_user)
