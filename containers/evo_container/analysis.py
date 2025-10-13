"""Analytical stage for Evo Container pipelines."""

from __future__ import annotations

from statistics import mean
from typing import Dict, List


def analyze_link(state: Dict[str, object]) -> Dict[str, object]:
    """Derive lightweight metrics from the intake summary."""

    if "intake" not in state:
        raise ValueError("analysis requires intake data")

    link = str(state["intake"]["link"])
    insights: List[str] = list(state.get("insights", []))

    heuristic_scores = [
        float(len(link) % 10) / 10.0,
        0.6 if "https" in link else 0.3,
        0.5 if link.endswith("/share") or "chat.openai" in link else 0.4,
    ]
    coherence = round(mean(heuristic_scores), 3)

    updated = {**state}
    updated["analysis"] = {
        "coherence_estimate": coherence,
        "signal_strength": heuristic_scores[0],
        "security_weight": heuristic_scores[1],
        "context_relevance": heuristic_scores[2],
    }
    updated.setdefault("stages", []).append(
        {
            "stage": "analysis",
            "status": "completed",
        }
    )
    insights.append(
        "Derived coherence score {:.3f} based on heuristic link metrics.".format(
            coherence
        )
    )
    updated["insights"] = insights

    return updated


__all__ = ["analyze_link"]
