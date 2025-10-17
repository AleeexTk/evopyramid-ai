"""Module I router for EvoPyramid API."""

from __future__ import annotations

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
    """Return Module I availability details."""

    return {
        "status": "active",
        "module": "Module I",
        "capabilities": ["reasoning", "analysis", "planning"],
    }


@router.post("/analyze")
async def analyze_with_module_i(query: ModuleIQuery) -> Dict[str, Any]:
    """Basic stub for Module I analysis."""

    return {
        "analysis": f"Module I analysis for: {query.question}",
        "context": query.context,
    }


__all__ = [
    "router",
    "ModuleIQuery",
]
