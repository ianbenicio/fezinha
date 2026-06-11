"""Fezinha API — entrypoint.

Rodar: uvicorn api.main:app --reload
Docs:  http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalog, credits, profile, queries

app = FastAPI(
    title="Fezinha API",
    version="0.1.0",
    description="Plataforma de análise de partidas — auth, créditos, consultas, catálogo.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev; ajustar em produção
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
