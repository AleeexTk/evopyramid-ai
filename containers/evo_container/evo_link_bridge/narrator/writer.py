"""Chronicle writer for EvoLink narratives."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ... import ensure_directory

LOG_DIRECTORY = Path(__file__).resolve().parents[4] / "logs" / "chronicles"


def write_chronicle(content: str) -> Path:
    """Persist a chronicle file and return its path."""

    ensure_directory(LOG_DIRECTORY)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = LOG_DIRECTORY / f"evochronicle_{timestamp}.txt"
    path.write_text(content, encoding="utf-8")
    return path
