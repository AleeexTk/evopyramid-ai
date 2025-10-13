"""Intake stage for Evo Container pipelines."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext


DEFAULT_CHANNEL = "intake"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Collect the raw payload and register it inside the context."""

    config = config or {}
    payload = {
        "link": context.link or config.get("link"),
        "profile": context.profile or config.get("profile"),
        "source": config.get("source", "manual"),
    }
    context.update_state("intake", payload)
    context.log_event(DEFAULT_CHANNEL, "captured external payload", **payload)
    return payload
