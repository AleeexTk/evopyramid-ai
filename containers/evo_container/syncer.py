"""Synchronization stage bridging the container with archival systems."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext

CHANNEL = "sync"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Persist integration artefacts for downstream observers."""

    config = config or {}
    integrated = context.state.get("integrate", {})
    archive_record = {
        "observer": config.get("observer", "trinity"),
        "memory_channel": integrated.get("memory_channel"),
        "intensity": integrated.get("intensity"),
    }
    context.update_state("sync", archive_record)
    context.log_event(CHANNEL, "synchronized with observers", **archive_record)
    return archive_record
