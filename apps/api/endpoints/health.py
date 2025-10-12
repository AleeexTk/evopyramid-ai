"""Маршруты для health/readiness проверок."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.config import settings
from apps.core.flow.context_engine import get_context_engine
from apps.core.memory.memory_manager import Memory
from apps.core.observers.trinity_observer import trinity_observer

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, object]:
    """Production health check с метриками системы."""

    trinity_state = await trinity_observer.get_current_state()
    return {
        "status": "healthy",
        "timestamp": trinity_state["timestamp"],
        "system": {
            "trinity_coherence": trinity_state["system_state"]["temporal_coherence"],
            "observer_mode": trinity_state["observer_mode"],
            "active_agents": trinity_state["statistics"]["active_agents"],
        },
        "environment": settings.environment,
    }


@router.get("/readiness")
async def readiness_probe() -> dict[str, object]:
    """Kubernetes readiness probe."""

    checks = {
        "memory_manager": await _check_memory(),
        "trinity_observer": await _check_trinity(),
        "context_engine": await _check_context_engine(),
    }
    all_healthy = all(checks.values())
    return {"ready": all_healthy, "checks": checks}


async def _check_memory() -> bool:
    try:
        return await Memory.ping()
    except Exception:
        return False


async def _check_trinity() -> bool:
    try:
        state = await trinity_observer.get_current_state()
        return state["statistics"]["total_observations"] >= 0
    except Exception:
        return False


async def _check_context_engine() -> bool:
    try:
        engine = get_context_engine()
        stats = engine.get_stats()
        return stats["total_queries"] >= 0
    except Exception:
        return False


__all__ = ["router"]
