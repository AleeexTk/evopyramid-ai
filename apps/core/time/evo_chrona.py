"""EvoChrona orchestrates Kairos moments and persistence hooks."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol

__all__ = ["EvoChrona", "sanitize_moment_key"]

# Windows file names cannot include any of the characters below.  We keep the
# list deliberately small and targeted to avoid overly aggressive replacements.
_FORBIDDEN_FS_CHARS = set('<>:"/\\|?*')


class MemoryWriter(Protocol):
    """Protocol describing the minimal storage API required by EvoChrona."""

    def save_state(self, key: str, payload: Mapping[str, Any]) -> None:
        """Persist the given payload under the provided key."""


def sanitize_moment_key(candidate: str, *, replacement: str = "_") -> str:
    """Return a filesystem-safe key derived from ``candidate``.

    Parameters
    ----------
    candidate:
        Raw key generated from the Kairos moment timestamp.
    replacement:
        Character used to replace forbidden characters.  Defaults to an
        underscore so the sanitized key remains readable.
    """

    sanitized_parts: list[str] = []
    for char in candidate:
        if char in _FORBIDDEN_FS_CHARS or char.isspace():
            sanitized_parts.append(replacement)
        else:
            sanitized_parts.append(char)
    sanitized = "".join(sanitized_parts).strip()
    # Windows does not allow names ending in a dot or space; guard against the
    # case where the raw key might include trailing punctuation.
    sanitized = sanitized.rstrip(". ")
    return sanitized or replacement


class EvoChrona:
    """Kairos moment orchestrator used to persist significant time events."""

    def __init__(self, memory: MemoryWriter) -> None:
        self._memory = memory

    def _derive_moment_key(self, moment: datetime) -> str:
        iso_moment = moment.isoformat(timespec="seconds")
        return sanitize_moment_key(iso_moment)

    def _save_kairos_moment(
        self,
        moment: datetime,
        payload: Mapping[str, Any],
    ) -> str:
        """Persist a Kairos moment snapshot via the configured memory backend."""

        safe_key = self._derive_moment_key(moment)
        self._memory.save_state(safe_key, payload)
        return safe_key
