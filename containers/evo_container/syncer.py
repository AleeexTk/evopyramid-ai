"""Synchronization stage for EvoContainer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping

TELEMETRY_CHANNELS = ["memory_journal", "trinity_observer", "soul_sync"]


def run(context: MutableMapping[str, object]) -> None:
    """Describe synchronization targets for the integration contract."""

    contract = context.get("integration_contract", {})
    sync_targets = {
        "channels": TELEMETRY_CHANNELS,
        "primary_contract": contract,
    }
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "sync",
            "targets": sync_targets,
            "timestamp": timestamp,
            "note": "Identified telemetry channels for synchronization.",
        }
    )
    context["sync_targets"] = sync_targets
    context["last_updated"] = timestamp
