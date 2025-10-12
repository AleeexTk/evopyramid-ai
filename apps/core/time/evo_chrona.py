import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Callable, Awaitable, List
import json


class TemporalState(Enum):
    ACTIVE_FLOW = "active_flow"
    DEEP_FOCUS = "deep_focus"
    REFLECTIVE = "reflective"
    IDLE_COOLING = "idle_cooling"
    DREAMING = "dreaming"


PulseHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class EvoChrona:
    """Пульс времени + саморефлексия + регулировка темпа."""

    def __init__(self) -> None:
        self.current_time = datetime.utcnow()
        self.tempo = 1.0
        self.drift = 0.0
        self.temporal_state = TemporalState.ACTIVE_FLOW
        self._pulse_handlers: List[PulseHandler] = []
        self.self_awareness_interval = 60  # импульсов
        self.kairos_snapshots: List[Dict[str, Any]] = []
        self.flow_coherence_history: List[Dict[str, Any]] = []

    async def pulse(self) -> None:
        pulse_count = 0
        try:
            while True:
                await asyncio.sleep(max(0.05, 1.0 * self.tempo))
                self.current_time = datetime.utcnow() + timedelta(seconds=self.drift)
                pulse_count += 1
                await self._broadcast_pulse(
                    {
                        "timestamp": self.current_time.isoformat(),
                        "pulse_count": pulse_count,
                        "tempo": self.tempo,
                        "temporal_state": self.temporal_state.value,
                    }
                )
                if pulse_count % self.self_awareness_interval == 0:
                    await self._trigger_self_awareness()
        except asyncio.CancelledError:
            raise

    def register_pulse_handler(self, handler: PulseHandler) -> None:
        self._pulse_handlers.append(handler)

    def unregister_pulse_handler(self, handler: PulseHandler) -> None:
        if handler in self._pulse_handlers:
            self._pulse_handlers.remove(handler)

    async def _broadcast_pulse(self, pulse_data: Dict[str, Any]) -> None:
        for handler in list(self._pulse_handlers):
            try:
                await handler(pulse_data)
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[EvoChrona] pulse handler error: {exc}")

    async def _trigger_self_awareness(self) -> None:
        try:
            from apps.core.monitoring.flow_monitor import FlowMonitor

            flow_state = FlowMonitor.get_current_flow()
            coherence = flow_state.get("coherence", 0.5)
            self.flow_coherence_history.append(
                {
                    "timestamp": self.current_time.isoformat(),
                    "coherence": coherence,
                }
            )
            if coherence > 0.8:
                snap = {
                    "timestamp": self.current_time.isoformat(),
                    "coherence": coherence,
                    "state": self.temporal_state.value,
                    "signature": self._temporal_signature(),
                }
                self.kairos_snapshots.append(snap)
                await self._save_kairos_moment(snap)
                print(
                    f"🌀 EvoChrona: Kairos snapshot captured (coherence {coherence:.2f})"
                )
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EvoChrona] self-awareness error: {exc}")

    def _temporal_signature(self) -> str:
        recent = self.flow_coherence_history[-10:]
        avg = sum(h["coherence"] for h in recent) / len(recent) if recent else 0.0
        payload = {
            "state": self.temporal_state.value,
            "avg_coherence": round(avg, 3),
            "tempo": self.tempo,
            "moment_type": "peak" if avg > 0.7 else "valley",
        }
        return json.dumps(payload, sort_keys=True)

    async def _save_kairos_moment(self, snap: Dict[str, Any]) -> None:
        try:
            from apps.core.memory.memory_manager import Memory

            await Memory.save_state(
                key=f"kairos_{snap['timestamp']}",
                data=snap,
                category="temporal_awareness",
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EvoChrona] save kairos error: {exc}")

    def adjust_tempo(self, new_tempo: float) -> None:
        self.tempo = max(0.1, min(3.0, float(new_tempo)))
        print(f"🎵 EvoChrona tempo → {self.tempo}x")

    def change_temporal_state(self, new_state: TemporalState) -> None:
        self.temporal_state = new_state
        print(f"🌊 EvoChrona state → {new_state.value}")


chrona = EvoChrona()
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
