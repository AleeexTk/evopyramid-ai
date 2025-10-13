"""Adaptation stage for Evo Container pipelines."""

from __future__ import annotations

from typing import Dict, List


ADAPTATION_RULES: Dict[str, str] = {
    "evochka": "emergent", "eva_absolute": "strategic", "eva_archivarius": "archival", "eva_architect": "design"
}


def adapt_for_memory(state: Dict[str, object]) -> Dict[str, object]:
    """Prepare analyzed payload for memory ingestion."""

    if "analysis" not in state:
        raise ValueError("adaptation requires analysis data")

    profile = str(state.get("profile", "unknown"))
    style = ADAPTATION_RULES.get(profile, "hybrid")

    updated = {**state}
    adaptation = {
        "profile": profile,
        "style": style,
        "guidance": _guidance_for_style(style),
    }
    updated["adaptation"] = adaptation

    notes: List[str] = list(updated.get("insights", []))
    notes.append(f"Profile {profile} mapped to {style} adaptation mode.")
    updated["insights"] = notes
    updated.setdefault("stages", []).append(
        {
            "stage": "adapt",
            "status": "completed",
        }
    )

    return updated


def _guidance_for_style(style: str) -> str:
    mapping = {
        "emergent": "Blend narrative tone with exploratory detail.",
        "strategic": "Highlight outcomes and measurable signals.",
        "archival": "Preserve chronological fidelity and sources.",
        "design": "Connect insights to architectural choices.",
        "hybrid": "Balance technical trace with reflective notes.",
    }
    return mapping.get(style, mapping["hybrid"])


__all__ = ["adapt_for_memory"]
