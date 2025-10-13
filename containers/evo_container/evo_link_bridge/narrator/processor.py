"""Narrator processor orchestrating chronicle creation."""

from __future__ import annotations

from typing import Dict

from . import commentator, writer


def create_chronicle(state: Dict[str, object]) -> Dict[str, object]:
    """Generate a chronicle and augment the pipeline state with metadata."""

    narrative = commentator.compose_commentary(state)
    path = writer.write_chronicle(state, narrative)

    updated = {**state}
    updated.setdefault("stages", []).append(
        {
            "stage": "narrate",
            "status": "completed",
            "artifact": str(path),
        }
    )
    updated["chronicle"] = {
        "path": str(path),
        "narrative": narrative,
    }
    updated.setdefault("insights", []).append(
        "Chronicle captured at {path}.".format(path=path)
    )

    return updated


__all__ = ["create_chronicle"]
