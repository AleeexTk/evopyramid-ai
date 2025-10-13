"""Final harmonisation pass for Evo Container pipelines."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext

CHANNEL = "harmonize"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Produce a consolidated output summary for narrators and soul sync."""

    config = config or {}
    summary = {
        "profile": context.state.get("intake", {}).get("profile"),
        "intensity": context.state.get("integrate", {}).get("intensity"),
        "observer": context.state.get("sync", {}).get("observer"),
        "tone": config.get("tone", "contemplative"),
    }
    context.update_state("harmonize", summary)
    context.log_event(CHANNEL, "harmonized container output", **summary)
    return summary
