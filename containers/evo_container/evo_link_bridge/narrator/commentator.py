"""Commentator responsible for translating events into narrative."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping


def _format_event(event: Mapping[str, object]) -> str:
    stage = event.get("stage", "unknown")
    note = event.get("note", "")
    timestamp = event.get("timestamp", datetime.now(tz=timezone.utc).isoformat())
    return f"[{timestamp}] {stage.upper()}: {note}"


def compose_story(context: MutableMapping[str, object]) -> str:
    """Compose a textual chronicle from the pipeline context."""

    header = [
        "EvoLink Chronicle",
        "==================",
        f"Profile: {context.get('profile') or 'unknown'}",
        f"Link: {context.get('link') or 'n/a'}",
        "",
    ]
    events: Iterable[Mapping[str, object]] = context.get("events", [])
    body = [_format_event(event) for event in events]
    if not body:
        body.append("No events were recorded during this pipeline execution.")

    footer = ["", "-- EvoLink Narrator"]
    return "\n".join(header + body + footer)


__all__ = ["compose_story"]
