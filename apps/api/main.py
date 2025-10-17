"""FastAPI приложение EvoPyramid."""

from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings
from .endpoints import agents, health as legacy_health, metrics

logger = logging.getLogger("evo.api")

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

trusted_hosts: List[str] = list(settings.trusted_hosts)
if settings.debug and "*" not in trusted_hosts:
    trusted_hosts.append("*")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Основные роутеры EvoPyramid API
app.include_router(legacy_health.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(agents.router, prefix="/api")

try:
    from apps.api.routers import codex, module_i
except Exception as exc:  # pragma: no cover - optional routers
    logger.exception("Router loading failed: %s", exc)
else:
    app.include_router(codex.router)
    app.include_router(module_i.router)
    logger.info("✅ Codex and Module I routers loaded")


@app.get("/")
async def root() -> dict[str, object]:
    """Health information for root endpoint."""

    return {
        "message": "EvoPyramid API is running",
        "version": settings.api_version,
        "endpoints": ["/codex", "/module_i", "/api/agents", "/api/metrics", "/api/health"],
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Lightweight health endpoint for infrastructure probes."""

    return {"status": "healthy", "service": "EvoPyramid API"}


__all__ = ["app"]
