"""Final harmonization stage for Evo Container pipelines."""

from __future__ import annotations

from statistics import mean
from typing import Dict, List


HARMONY_THRESHOLD = 0.55


def harmonize_state(state: Dict[str, object]) -> Dict[str, object]:
    """Produce a consolidated pipeline summary."""

    if "analysis" not in state:
        raise ValueError("harmonization requires analysis data")

    coherence = float(state["analysis"].get("coherence_estimate", 0.0))
    integration_mode = state.get("integration", {}).get("mode", "hybrid")

    insights: List[str] = list(state.get("insights", []))
    insights.append(
        "Harmonized container state with mode {mode} and coherence {coherence:.3f}.".format(
            mode=integration_mode, coherence=coherence
        )
    )

    updated = {**state}
    updated["harmonized"] = {
        "coherence": coherence,
        "integrity": _integrity_score(state),
        "is_ready": coherence >= HARMONY_THRESHOLD,
        "mode": integration_mode,
    }
    updated["insights"] = insights
    updated.setdefault("stages", []).append(
        {
            "stage": "harmonize",
            "status": "completed",
        }
    )

    return updated


def _integrity_score(state: Dict[str, object]) -> float:
    components = [
        float("intake" in state),
        float("analysis" in state),
        float("adaptation" in state),
        float("integration" in state),
        float("sync" in state),
    ]
    return round(mean(components), 3)


__all__ = ["harmonize_state", "HARMONY_THRESHOLD"]
