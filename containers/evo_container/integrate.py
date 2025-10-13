"""Integration stage for EvoContainer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping


def run(context: MutableMapping[str, object]) -> None:
    """Merge adaptation insights into a unified integration contract."""

    plan = context.get("adaptation_plan", [])
    integration_contract = {
        "handoff": "memory",
        "profile": context.get("profile"),
        "actions": plan,
    }
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "integrate",
            "contract": integration_contract,
            "timestamp": timestamp,
            "note": "Prepared integration hand-off for downstream systems.",
        }
    )
    context["integration_contract"] = integration_contract
    context["last_updated"] = timestamp
