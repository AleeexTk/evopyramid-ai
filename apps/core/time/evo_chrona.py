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
