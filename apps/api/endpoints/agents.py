"""Маршруты взаимодействия с агентами EvoPyramid."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.api.dependencies import verify_api_key
from apps.core.flow.context_engine import QuantumContext
from apps.core.observers.trinity_observer import trinity_observer

from .metrics import REQUESTS_COUNT, REQUEST_DURATION

router = APIRouter(tags=["agents"])


class AgentRequest(BaseModel):
    intent: str
    context: Dict[str, Any] | None = None
    mode: str = "default"


class AgentResponse(BaseModel):
    response: Dict[str, Any]
    coherence: float
    trace_id: str


@router.post("/soul/design", response_model=AgentResponse)
async def soul_design(
    request: AgentRequest, api_key: str = Depends(verify_api_key)
) -> AgentResponse:
    """Soul node: архитектурное проектирование."""

    del api_key  # подтверждение использования, значение не требуется далее

    REQUESTS_COUNT.inc()
    start_time = time.perf_counter()

    try:
        context = await QuantumContext.process(request.intent, request.context or {})
        await trinity_observer.record_interaction("soul", context.trace_id)
        duration = time.perf_counter() - start_time
        REQUEST_DURATION.observe(duration)
        return AgentResponse(
            response=context.design,
            coherence=context.coherence,
            trace_id=context.trace_id,
        )
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        raise HTTPException(status_code=500, detail=f"Design error: {exc}") from exc


__all__ = ["router", "AgentRequest", "AgentResponse"]
