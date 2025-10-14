"""Core heartbeat endpoints for EvoPyramid API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def ping() -> Dict[str, Any]:
    """Return a minimal heartbeat payload for health probes."""

    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resonance": "coherent",
    }
