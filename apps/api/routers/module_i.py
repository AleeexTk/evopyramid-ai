"""Module I router for EvoPyramid API."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.core.module_i import ModuleIEngine

router = APIRouter(prefix="/module_i", tags=["module_i"])
LOGGER = logging.getLogger("evo.api.module_i")
ENGINE = ModuleIEngine()
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/module_i", tags=["module_i"])


class ModuleIQuery(BaseModel):
    """Payload for Module I analytical requests."""

    question: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
async def module_i_status() -> Dict[str, Any]:
    """Return Module I availability and telemetry details."""

    return ENGINE.status()
    """Return Module I availability details."""

    return {
        "status": "active",
        "module": "Module I",
        "capabilities": ["reasoning", "analysis", "planning"],
    }


@router.post("/analyze")
async def analyze_with_module_i(query: ModuleIQuery) -> Dict[str, Any]:
    """Run Module I analytical pipeline for the provided question."""

    try:
        analysis = await ENGINE.analyze(query.question, query.context)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Module I analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail="Module I processing failed") from exc

    return {
        "status": "success",
        "question": query.question,
        "analysis": analysis,
    """Basic stub for Module I analysis."""

    return {
        "analysis": f"Module I analysis for: {query.question}",
        "context": query.context,
    }


__all__ = [
    "router",
    "ModuleIQuery",
]
