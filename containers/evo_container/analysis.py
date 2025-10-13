"""Analytical routines for Evo Container pipelines."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext

CHANNEL = "analysis"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Derive analytical signals from the intake payload."""

    config = config or {}
    intake_payload = context.state.get("intake", {})
    insights = {
        "link_present": bool(intake_payload.get("link")),
        "profile": intake_payload.get("profile"),
        "hypothesis": config.get(
            "hypothesis",
            "Imported narrative fragment will reinforce collective memory.",
        ),
    }
    context.update_state("analysis", insights)
    context.log_event(CHANNEL, "derived intake insights", **insights)
    return insights
