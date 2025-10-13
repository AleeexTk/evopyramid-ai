"""Adaptive calibration stage."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext

CHANNEL = "adapt"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Translate analytical insights into adaptation directives."""

    config = config or {}
    analysis = context.state.get("analysis", {})
    directives = {
        "alignment_score": 1.0 if analysis.get("link_present") else 0.5,
        "mode": config.get("mode", "convergence"),
    }
    context.update_state("adapt", directives)
    context.log_event(CHANNEL, "generated adaptation directives", **directives)
    return directives
