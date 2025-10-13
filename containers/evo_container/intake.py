"""Intake stage for the EvoContainer pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping

Event = MutableMapping[str, object]


def run(context: MutableMapping[str, object]) -> None:
    """Register the external link and profile into the shared context."""

    link = context.get("link")
    profile = context.get("profile")
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "intake",
            "link": link,
            "profile": profile,
            "timestamp": timestamp,
            "note": "Captured incoming link for assimilation.",
        }
    )
    context["last_updated"] = timestamp
