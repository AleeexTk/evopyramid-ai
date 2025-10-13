"""Generate narrative commentary for Evo Container chronicles."""

from __future__ import annotations

from typing import Dict, Iterable, List


def compose_commentary(state: Dict[str, object]) -> str:
    """Create a textual chronicle from the pipeline state."""

    link = str(state.get("link", ""))
    profile = str(state.get("profile", "unknown"))
    coherence = float(state.get("analysis", {}).get("coherence_estimate", 0.0))
    mode = state.get("harmonized", {}).get("mode", "hybrid")
    ready = state.get("harmonized", {}).get("is_ready", False)
    insights: Iterable[str] = state.get("insights", [])  # type: ignore[assignment]
    stages: List[str] = [str(item.get("stage")) for item in state.get("stages", [])]

    readiness = "READY" if ready else "DRAFT"
    insights_text = "\n".join(f"- {line}" for line in insights)

    return (
        "Chronicle Status: {readiness}\n"
        "Profile: {profile}\n"
        "Link: {link}\n"
        "Pipeline Stages: {stages}\n"
        "Coherence: {coherence:.3f}\n"
        "Harmonization Mode: {mode}\n"
        "Insights:\n{insights}\n"
    ).format(
        readiness=readiness,
        profile=profile,
        link=link,
        stages=", ".join(stages),
        coherence=coherence,
        mode=mode,
        insights=insights_text or "- No insights captured",
    )


__all__ = ["compose_commentary"]
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
