"""FastAPI приложение EvoPyramid."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings
from .endpoints import agents, health, metrics

app = FastAPI(
    title="EvoPyramid API",
    description="Production API для мультиагентной системы EvoPyramid",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Мидлвари производственного уровня
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trusted_hosts = list(settings.trusted_hosts)
if settings.debug and "*" not in trusted_hosts:
    trusted_hosts.append("*")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Роутеры
app.include_router(health.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(agents.router, prefix="/api")


__all__ = ["app"]
