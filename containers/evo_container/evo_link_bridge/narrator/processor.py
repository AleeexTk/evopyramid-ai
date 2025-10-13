"""Processor for EvoLink Narrator."""

from __future__ import annotations

from typing import MutableMapping

from . import commentator, writer


def run(context: MutableMapping[str, object]) -> None:
    """Generate a chronicle entry from the pipeline context."""

    storyline = commentator.compose_story(context)
    chronicle_path = writer.write_chronicle(storyline)
    chronicles = context.setdefault("chronicles", [])
    chronicles.append(str(chronicle_path))
    summary = context.setdefault("summary", {})
    summary["chronicle_ready"] = True
    summary["chronicle_path"] = str(chronicle_path)
    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "narrate",
            "timestamp": writer.current_timestamp(),
            "note": "Rendered chronicle via EvoLink Narrator.",
            "chronicle": str(chronicle_path),
        }
    )
