"""Integration stage for Evo Container pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


def integrate_payload(state: Dict[str, object]) -> Dict[str, object]:
    """Aggregate adaptation with integration metadata."""

    if "adaptation" not in state:
        raise ValueError("integration requires adaptation data")

    updated = {**state}
    integration = {
        "integrated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": "memory.core",
        "mode": state["adaptation"]["style"],
    }
    updated["integration"] = integration
    updated.setdefault("stages", []).append(
        {
            "stage": "integrate",
            "status": "completed",
        }
    )
    updated.setdefault("insights", []).append(
        "Payload staged for memory.core ingestion with mode {mode}.".format(
            mode=integration["mode"]
        )
    )

    return updated


__all__ = ["integrate_payload"]
