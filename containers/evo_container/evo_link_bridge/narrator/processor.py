"""Narrator processor orchestrating chronicle creation."""
"""Process pipeline timelines into EvoLink chronicles."""

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
from ... import PipelineContext, iter_events
from . import commentator, writer

CHANNEL = "narrator"


def run(context: PipelineContext, config: Dict[str, str] | None = None) -> Dict[str, str]:
    """Generate a chronicle from the accumulated pipeline timeline."""

    config = config or {}
    commentary = commentator.compose_commentary(iter_events(context.timeline))
    chronicle_path = writer.write_chronicle(commentary)
    context.log_event(CHANNEL, "recorded chronicle", path=str(chronicle_path))

    result = {
        "chronicle_path": str(chronicle_path),
        "commentary": commentary,
        "persona": context.profile,
    }
    context.update_state("chronicle", result)

    if config.get("attach_to_metadata", True):
        context.extend_metadata(chronicle=result)

    return result
