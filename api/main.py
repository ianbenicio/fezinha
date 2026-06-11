"""Fezinha API — entrypoint.

Rodar: uvicorn api.main:app --reload
Docs:  http://localhost:8000/docs
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalog, credits, profile, queries

app = FastAPI(
    title="Fezinha API",
    version="0.1.0",
    description="Plataforma de análise de partidas — auth, créditos, consultas, catálogo.",
)

# Origens liberadas: env ALLOWED_ORIGINS (csv) + localhost por padrão.
# Em produção: setar ALLOWED_ORIGINS com o domínio Vercel.
_default_origins = "http://localhost:3000"
_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(credits.router)
app.include_router(queries.router)
app.include_router(catalog.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
