"""Integration stage for assimilating processed insights."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext

CHANNEL = "integrate"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Blend adaptation directives into the collective state."""

    config = config or {}
    directives = context.state.get("adapt", {})
    integrated = {
        "memory_channel": config.get("memory_channel", "core.memory"),
        "intensity": directives.get("alignment_score", 0.0) * config.get("gain", 1.0),
    }
    context.update_state("integrate", integrated)
    context.log_event(CHANNEL, "integrated directives", **integrated)
    return integrated
