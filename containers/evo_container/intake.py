"""Data intake stage for Evo Container pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass(slots=True)
class IntakeSummary:
    """Summary describing the result of the intake phase."""

    link: str
    profile: str
    collected_at: datetime
    status: str = "collected"

    def as_dict(self) -> Dict[str, str]:
        """Return a serializable representation."""

        return {
            "link": self.link,
            "profile": self.profile,
            "collected_at": self.collected_at.isoformat(timespec="seconds"),
            "status": self.status,
        }


def collect_link(state: Dict[str, object]) -> Dict[str, object]:
    """Capture the incoming link payload and timestamp it."""

    if "link" not in state:
        raise ValueError("pipeline state must include a 'link' value")
    if "profile" not in state:
        raise ValueError("pipeline state must include a 'profile' value")

    summary = IntakeSummary(
        link=str(state["link"]),
        profile=str(state["profile"]),
        collected_at=datetime.now(timezone.utc),
    )

    updated = {**state}
    updated.setdefault("stages", []).append(
        {
            "stage": "intake",
            "status": summary.status,
            "timestamp": summary.collected_at.isoformat(timespec="seconds"),
        }
    )
    updated["intake"] = summary.as_dict()
    updated.setdefault("insights", []).append(
        f"Captured link {summary.link} for profile {summary.profile}."
    )

    return updated


__all__ = ["collect_link", "IntakeSummary"]
"""Intake stage for Evo Container pipelines."""

from __future__ import annotations

from typing import Any, Dict

from . import PipelineContext


DEFAULT_CHANNEL = "intake"


def run(context: PipelineContext, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Collect the raw payload and register it inside the context."""

    config = config or {}
    payload = {
        "link": context.link or config.get("link"),
        "profile": context.profile or config.get("profile"),
        "source": config.get("source", "manual"),
    }
    context.update_state("intake", payload)
    context.log_event(DEFAULT_CHANNEL, "captured external payload", **payload)
    return payload
