"""Generate reflective commentary for container chronicles."""

from __future__ import annotations

from typing import Iterable


def compose_commentary(events: Iterable[str]) -> str:
    """Collapse structured events into an emotive commentary block."""

    lines = list(events)
    if not lines:
        return "No events were captured during this run."

    header = "EvoLink Narrator Summary"
    body = "\n".join(lines)
    return f"{header}\n{'-' * len(header)}\n{body}\n"
