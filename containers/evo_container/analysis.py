"""Analysis stage for EvoContainer pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping

KEYWORDS = {
    "research": ["paper", "study", "analysis"],
    "community": ["forum", "discussion", "thread"],
    "deployment": ["release", "deploy", "launch"],
}


def run(context: MutableMapping[str, object]) -> None:
    """Perform a lightweight semantic analysis of the ingested link."""

    link = (context.get("link") or "").lower()
    detected_tags = set()
    for tag, words in KEYWORDS.items():
        if any(word in link for word in words):
            detected_tags.add(tag)
    if not detected_tags:
        detected_tags.add("insight")

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    events = context.setdefault("events", [])
    events.append(
        {
            "stage": "analysis",
            "tags": sorted(detected_tags),
            "timestamp": timestamp,
            "note": "Performed heuristic analysis of the link context.",
        }
    )
    insights = set(context.get("insights", []))
    insights.update(detected_tags)
    context["insights"] = sorted(insights)
    context["last_updated"] = timestamp
