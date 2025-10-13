"""Adaptation stage for EvoContainer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping


def run(context: MutableMapping[str, object]) -> None:
    """Translate analysis insights into adaptation intents."""

    insights = context.get("insights", [])
    adaptation_plan = [f"align_{tag}" for tag in insights]
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "adapt",
            "plan": adaptation_plan,
            "timestamp": timestamp,
            "note": "Derived adaptation strategies from detected insights.",
        }
    )
    context["adaptation_plan"] = adaptation_plan
    context["last_updated"] = timestamp
