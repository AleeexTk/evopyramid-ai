"""Synchronization utilities for Evo Container pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


SYNC_CHANNEL = "containers/evo_container/evo_link_bridge/narrator/logs/chronicles"


def sync_memory(state: Dict[str, object]) -> Dict[str, object]:
    """Record synchronization metadata for the pipeline."""

    if "integration" not in state:
        raise ValueError("synchronization requires integration data")

    updated = {**state}
    sync_record = {
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "channel": SYNC_CHANNEL,
        "status": "pending-chronicle",
    }
    updated["sync"] = sync_record
    updated.setdefault("stages", []).append(
        {
            "stage": "sync",
            "status": "completed",
        }
    )

    notes = list(updated.get("insights", []))
    notes.append(
        "Synchronization metadata stored; awaiting chronicle creation via EvoLink narrator."
    )
    updated["insights"] = notes

    return updated


__all__ = ["sync_memory", "SYNC_CHANNEL"]
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
