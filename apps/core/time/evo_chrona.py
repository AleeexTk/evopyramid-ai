"""Temporal orchestration utilities for EvoPyramid."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Sequence


class TemporalState(Enum):
    """High-level temporal modes observed by the architecture."""

    ACTIVE_FLOW = "active_flow"
    DEEP_FOCUS = "deep_focus"
    REFLECTIVE = "reflective"
    IDLE_COOLING = "idle_cooling"
    DREAMING = "dreaming"


LegacyPulseHandler = Callable[[Dict[str, Any]], Awaitable[None]]
AsyncPulseHandler = Callable[[datetime], Awaitable[None] | None]


class _LegacyChrona:
    """Backward-compatible chrona used by the existing monitoring stack."""

    def __init__(self) -> None:
        self.current_time = datetime.utcnow()
        self.tempo = 1.0
        self.drift = 0.0
        self.temporal_state = TemporalState.ACTIVE_FLOW
        self._pulse_handlers: list[LegacyPulseHandler] = []
        self.self_awareness_interval = 60
        self.kairos_snapshots: list[Dict[str, Any]] = []
        self.flow_coherence_history: list[Dict[str, Any]] = []

    async def pulse(self) -> None:
        """Emit pulses until cancelled."""

        pulse_count = 0
        try:
            while True:
                await asyncio.sleep(max(0.05, 1.0 * self.tempo))
                self.current_time = datetime.utcnow() + timedelta(seconds=self.drift)
                pulse_count += 1
                payload = {
                    "timestamp": self.current_time.isoformat(),
                    "pulse_count": pulse_count,
                    "tempo": self.tempo,
                    "temporal_state": self.temporal_state.value,
                }
                await self._broadcast_pulse(payload)
                if pulse_count % self.self_awareness_interval == 0:
                    await self._trigger_self_awareness()
        except asyncio.CancelledError:
            raise

    def register_pulse_handler(self, handler: LegacyPulseHandler) -> None:
        if handler not in self._pulse_handlers:
            self._pulse_handlers.append(handler)

    def unregister_pulse_handler(self, handler: LegacyPulseHandler) -> None:
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

    def change_temporal_state(self, new_state: TemporalState) -> None:
        self.temporal_state = new_state


class EvoChrona:
    """Modern asynchronous chrona used by newer observability flows."""

    def __init__(
        self,
        base_interval: float = 1.0,
        *,
        tempo: float = 1.0,
        memory: Optional[Any] = None,
    ) -> None:
        if base_interval <= 0:
            raise ValueError("base_interval must be greater than zero")
        self.base_interval = base_interval
        self.tempo = tempo
        self._handlers: set[AsyncPulseHandler] = set()
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._pulse_count = 0
        self._memory = memory

    @property
    def pulse_count(self) -> int:
        return self._pulse_count

    def register_handler(self, handler: AsyncPulseHandler) -> None:
        self._handlers.add(handler)

    def unregister_handler(self, handler: AsyncPulseHandler) -> None:
        self._handlers.discard(handler)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run(), name="EvoChrona.run")

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def pulse(self) -> None:
        interval = self._compute_interval()
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise
        self._pulse_count += 1
        await self._notify_handlers()

    async def _run(self) -> None:
        try:
            while self._running:
                await self.pulse()
        except asyncio.CancelledError:
            raise

    def _compute_interval(self) -> float:
        return max(0.02, self.base_interval / max(self.tempo, 0.1))

    async def _notify_handlers(self) -> None:
        timestamp = datetime.now(UTC)
        for handler in list(self._handlers):
            try:
                result = handler(timestamp)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[AsyncEvoChrona] handler error: {exc}")

    def _persist(self, key: str, payload: Mapping[str, Any]) -> None:
        if self._memory is None:
            return
        try:
            self._memory.save_state(key, payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[AsyncEvoChrona] memory error: {exc}")

    def _default_key(self, moment: datetime) -> str:
        return sanitize_moment_key(moment.isoformat())

    def _save_kairos_moment(self, moment: datetime, payload: Mapping[str, Any]) -> str:
        key = self._default_key(moment)
        self._persist(key, payload)
        return key


def sanitize_moment_key(raw: str) -> str:
    """Return a filesystem-safe representation of the provided key."""

    forbidden: Sequence[str] = tuple('<>:"/\\|?*')
    sanitized = raw
    for char in forbidden:
        sanitized = sanitized.replace(char, "_")
    sanitized = sanitized.replace(" ", "_")
    return sanitized


chrona = _LegacyChrona()


__all__ = ["EvoChrona", "TemporalState", "chrona", "sanitize_moment_key"]
