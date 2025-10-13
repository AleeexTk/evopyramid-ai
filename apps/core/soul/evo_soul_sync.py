"""Soul sync reflection engine for EvoPyramid."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[3]
CHRONICLE_DIRECTORY = REPO_ROOT / "containers" / "evo_container" / "evo_link_bridge" / "narrator" / "logs" / "chronicles"
SOUL_LOG = REPO_ROOT / "logs" / "soul_sync.log"


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _chronicle_paths() -> List[Path]:
    if not CHRONICLE_DIRECTORY.exists():
        return []
    return sorted(p for p in CHRONICLE_DIRECTORY.glob("evochronicle_*.txt") if p.is_file())


def _extract_stages(lines: Iterable[str]) -> List[str]:
    stages: List[str] = []
    for line in lines:
        if line.startswith("[") and "]" in line:
            fragment = line.split("]", 1)[-1].strip()
            if ":" in fragment:
                stage_fragment = fragment.split(":", 1)[0]
                stages.append(stage_fragment.lower())
    return stages


def build_reflection() -> dict:
    """Create a reflection snapshot from the latest chronicles."""

    chronicles = _chronicle_paths()
    timestamp = _iso_now()
    if not chronicles:
        return {
            "timestamp": timestamp,
            "status": "idle",
            "chronicle_count": 0,
            "latest": None,
            "stages": [],
            "mood": "dormant",
        }

    latest = chronicles[-1]
    text = latest.read_text(encoding="utf-8")
    lines = text.splitlines()
    stages = _extract_stages(lines)
    unique_stages = sorted(set(stages))
    mood = "synthesising" if "harmonize" in unique_stages else "observing"

    return {
        "timestamp": timestamp,
        "status": "active",
        "chronicle_count": len(chronicles),
        "latest": str(latest.relative_to(REPO_ROOT)),
        "stages": unique_stages,
        "mood": mood,
    }


def write_reflection(snapshot: dict) -> Path:
    """Append the reflection snapshot to the soul sync log."""

    SOUL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SOUL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return SOUL_LOG


def main() -> None:
    snapshot = build_reflection()
    log_path = write_reflection(snapshot)
    print(f"Soul sync snapshot stored at {log_path}:")
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
