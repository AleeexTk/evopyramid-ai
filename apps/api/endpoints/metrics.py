"""Prometheus-совместимые метрики."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest

from apps.core.observers.trinity_observer import trinity_observer

router = APIRouter(tags=["metrics"])

REQUESTS_COUNT = Counter("evopyramid_requests_total", "Total API requests")
REQUEST_DURATION = Histogram(
    "evopyramid_request_duration_seconds", "Request duration"
)
ACTIVE_AGENTS = Gauge("evopyramid_active_agents", "Active agents count")


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus-совместимые метрики."""

    state = await trinity_observer.get_current_state()
    ACTIVE_AGENTS.set(state["statistics"]["active_agents"])
    payload = generate_latest()
    return Response(payload, media_type=CONTENT_TYPE_LATEST)


__all__ = [
    "router",
    "REQUESTS_COUNT",
    "REQUEST_DURATION",
    "ACTIVE_AGENTS",
]
