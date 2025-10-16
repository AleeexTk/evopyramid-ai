"""Memory preservation endpoints for EvoPyramid API."""

from __future__ import annotations

from api.schemas.base import KairosMoment


def store(moment: KairosMoment) -> dict[str, str]:
    """Return acknowledgement for stored Kairos moment."""

    return {
        "status": "accepted",
        "moment_id": moment.identifier,
        "resonance": moment.resonance,
    }
