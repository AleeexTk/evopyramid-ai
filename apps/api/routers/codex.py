"""Codex router exposing EvoPyramid Codex capabilities."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.core.codex_core import (
    CodexProcessor,
    get_recent_entries,
    get_sync_status,
    get_system_health,
    propose_action,
)

logger = logging.getLogger("evo.api.codex")

router = APIRouter(prefix="/codex", tags=["codex"])


class CodexQuery(BaseModel):
    """Schema for Codex conversation requests."""

    message: str = Field(..., min_length=1, description="User prompt for Codex")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional context payload")


class CodexAction(BaseModel):
    """Schema representing an action proposal handled by Codex."""

    action_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    risk: List[str] = Field(default_factory=list)
    alternatives: List[str] = Field(default_factory=list)


@router.get("/status")
async def get_codex_status() -> Dict[str, Any]:
    """Return Codex runtime status and sync health."""

    try:
        return {
            "status": "active",
            "sync_status": get_sync_status(),
            "system_health": get_system_health(),
            "version": "1.0",
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Codex status error: %s", exc)
        return {"status": "error", "message": str(exc)}


@router.post("/query")
async def query_codex(query: CodexQuery) -> Dict[str, Any]:
    """Send a query to the Codex processor."""

    processor = CodexProcessor()
    try:
        response = await processor.process_query(query.message, context=query.context)
        return {
            "status": "success",
            "response": response,
            "query": query.message,
        }
    except Exception as exc:  # pragma: no cover - handled at runtime
        logger.exception("Codex query error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/propose")
async def propose_codex_action(action: CodexAction) -> Dict[str, Any]:
    """Register a proposed action via Codex."""

    try:
        result = propose_action(
            action_name=action.action_name,
            description=action.description,
            risk=action.risk,
            alternatives=action.alternatives,
        )
        return {
            "status": "proposed",
            "action_id": result.get("action_id"),
            "message": "Action successfully proposed and logged",
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Codex propose error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chronicles/recent")
async def get_recent_chronicles(limit: int = 10) -> Dict[str, Any]:
    """Return the latest Codex chronicle entries."""

    try:
        entries = get_recent_entries(limit=limit)
        return {"chronicles": entries, "count": len(entries)}
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Chronicles retrieval error: %s", exc)
        return {"chronicles": [], "error": str(exc)}


__all__ = [
    "router",
    "CodexQuery",
    "CodexAction",
]
