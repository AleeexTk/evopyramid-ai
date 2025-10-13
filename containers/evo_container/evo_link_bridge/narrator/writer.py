"""Chronicle writer for Evo Container pipelines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

LOG_DIR = Path("containers/evo_container/evo_link_bridge/narrator/logs/chronicles")


def write_chronicle(state: Dict[str, object], narrative: str) -> Path:
    """Persist the chronicle narrative to disk with metadata."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    filename = f"evochronicle_{timestamp}.txt"
    path = LOG_DIR / filename

    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": state.get("profile"),
        "link": state.get("link"),
        "coherence": state.get("analysis", {}).get("coherence_estimate"),
        "mode": state.get("harmonized", {}).get("mode"),
        "ready": state.get("harmonized", {}).get("is_ready"),
        "stages": [item.get("stage") for item in state.get("stages", [])],
    }

    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        handle.write(narrative)

    return path


__all__ = ["write_chronicle", "LOG_DIR"]
