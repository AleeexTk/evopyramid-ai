"""Asynchronous chrono pulse scheduler."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Optional

PulseHandler = Callable[[datetime], Awaitable[None] | None]


class EvoChrona:
    """Emit periodic pulses while respecting a configurable tempo."""

    def __init__(
        self,
        base_interval: float = 1.0,
        *,
        tempo: float = 1.0,
    ) -> None:
        if base_interval <= 0:
            raise ValueError("base_interval must be greater than zero")
        self.base_interval = base_interval
        self.tempo = tempo
        self._handlers: set[PulseHandler] = set()
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._pulse_count = 0

    @property
    def pulse_count(self) -> int:
        """Return the number of emitted pulses."""

        return self._pulse_count

    def register_handler(self, handler: PulseHandler) -> None:
        """Register a callback that receives pulse timestamps."""

        self._handlers.add(handler)

    def unregister_handler(self, handler: PulseHandler) -> None:
        """Remove a previously registered callback."""

        self._handlers.discard(handler)

    async def start(self) -> None:
        """Start emitting pulses until :meth:`stop` is called."""

        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run(), name="EvoChrona.run")

    async def stop(self) -> None:
        """Stop emitting pulses and await the background loop."""

        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def pulse(self) -> None:
        """Wait for the current interval and notify handlers."""

        interval = self._compute_interval()
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            # Surface cancellation to the caller while keeping state consistent.
            raise
        self._pulse_count += 1
        timestamp = datetime.now(UTC)
        for handler in list(self._handlers):
            result = handler(timestamp)
            if asyncio.iscoroutine(result):
                await result

    async def _run(self) -> None:
        try:
            while self._running:
                await self.pulse()
        except asyncio.CancelledError:
            pass

    def _compute_interval(self) -> float:
        tempo = max(self.tempo, 1e-6)
        interval = self.base_interval / tempo
        return max(0.05, interval)
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
        """Return a sanitized storage key derived from ``moment``."""

        formatted = moment.strftime("%Y-%m-%dT%H_%M_%S")
        tz_offset = moment.strftime("%z")
        if tz_offset:
            formatted = f"{formatted}{tz_offset}"
        return sanitize_moment_key(formatted)

    def _save_kairos_moment(
        self,
        moment: datetime,
        payload: Mapping[str, Any],
    ) -> str:
        """Persist a Kairos moment snapshot via the configured memory backend."""

        safe_key = self._derive_moment_key(moment)
        self._memory.save_state(safe_key, payload)
        return safe_key
