"""Harmonisation stage for EvoContainer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping


def run(context: MutableMapping[str, object]) -> None:
    """Summarise the pipeline execution into a compact snapshot."""

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    events = context.get("events", [])
    summary = {
        "link": context.get("link"),
        "profile": context.get("profile"),
        "insights": context.get("insights", []),
        "actions": context.get("adaptation_plan", []),
        "chronicle_ready": False,
        "completed_at": timestamp,
    }
    events.append(
        {
            "stage": "harmonize",
            "timestamp": timestamp,
            "note": "Compiled final summary and prepared for narration.",
        }
    )
    context["summary"] = summary
    context["last_updated"] = timestamp
