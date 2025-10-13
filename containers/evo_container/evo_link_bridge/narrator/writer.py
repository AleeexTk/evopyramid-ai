"""Writer for EvoLink chronicles."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

LOG_DIRECTORY = Path(__file__).resolve().parent / "logs" / "chronicles"


def current_timestamp() -> str:
    """Return the current timestamp in ISO 8601 format."""

    return datetime.now(tz=timezone.utc).isoformat()


def _build_filename() -> str:
    timestamp = datetime.now(tz=timezone.utc)
    return f"evochronicle_{timestamp.strftime('%Y%m%dT%H%M%SZ')}".replace("::", "-") + ".txt"


def write_chronicle(story: str) -> Path:
    """Persist the chronicle to disk and return the resulting path."""

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = _build_filename()
    path = LOG_DIRECTORY / filename
    path.write_text(story, encoding="utf-8")
    return path


__all__ = ["current_timestamp", "write_chronicle"]
