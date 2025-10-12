import asyncio
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import os

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


class EWAWatcher:
    """Evented-Watcher: ведёт сессию, реагируя на пульс Chrona и состояние потока."""

    def __init__(self, session_id: str, duration: str = "40m", mode: str = "session") -> None:
        self.session_id = session_id
        self.duration = self._parse_duration(duration)
        self.mode = mode
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + self.duration
        self.events: List[Dict[str, Any]] = []
        self.current_flow_state = {
            "coherence": 0.5,
            "soul_resonance": 0.5,
            "density": "medium",
            "tempo": "stable",
        }
        from apps.core.time.evo_chrona import chrona

        self._chrona = chrona
        self._chrona.register_pulse_handler(self._on_chrono_pulse)
        self._tasks: List[asyncio.Task] = []
        self._memory: Optional[Any] = None
        self.monitor_interval = 30.0
        self._active = False
        self._finalized = False

    def _parse_duration(self, raw: str) -> timedelta:
        raw = raw.strip().lower()
        if raw.endswith("m"):
            return timedelta(minutes=int(raw[:-1] or 0))
        if raw.endswith("h"):
            return timedelta(hours=int(raw[:-1] or 0))
        return timedelta(minutes=40)

    async def start(self, memory) -> None:
        self._memory = memory
        self._active = True
        print(f"🕰 EWA: session {self.session_id} for {self.duration}")
        self._tasks = [
            asyncio.create_task(self._monitor_flow()),
            asyncio.create_task(self._session_timer()),
        ]

    async def _on_chrono_pulse(self, pulse: Dict[str, Any]) -> None:
        if not self._active:
            return
        remaining = self.end_time - datetime.utcnow()
        if remaining < self.duration * 0.25:
            if self.current_flow_state.get("coherence", 0.0) > 0.6:
                await self._autosave("session_nearing_end")

    async def _monitor_flow(self) -> None:
        try:
            while self._active:
                await asyncio.sleep(self.monitor_interval)
                if not self._active:
                    break
                from apps.core.monitoring.flow_monitor import FlowMonitor

                flow = FlowMonitor.get_current_flow()
                self.current_flow_state.update(
                    {
                        "coherence": flow.get("coherence", 0.5),
                        "soul_resonance": flow.get("soul_resonance", 0.5),
                    }
                )
                density = (
                    "low"
                    if len(self.events) < 3
                    else ("high" if len(self.events) > 20 else "medium")
                )
                self.current_flow_state["density"] = density
                self.current_flow_state["tempo"] = "stable"
                if self.current_flow_state["coherence"] < 0.3 and density == "low":
                    await self._autosave("flow_dip_detected")
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EWA] monitor error: {exc}")

    async def _session_timer(self) -> None:
        try:
            await asyncio.sleep(self.duration.total_seconds())
            await self._finalize()
        except asyncio.CancelledError:
            raise

    def capture_event(self, event_type: str, data: Dict[str, Any]) -> None:
        self.events.append(
            {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                "flow_state": dict(self.current_flow_state),
            }
        )

    async def _autosave(self, reason: str) -> None:
        snap = {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "flow_state": dict(self.current_flow_state),
            "events_count": len(self.events),
            "duration_so_far": str(datetime.utcnow() - self.start_time),
        }
        await self._save_yaml(snap, suffix="autosave")

    async def _finalize(self) -> None:
        if self._finalized:
            return
        self._finalized = True
        self._active = False

        payload = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_events": len(self.events),
            "final_flow_state": dict(self.current_flow_state),
        }
        await self._save_yaml(payload, suffix="final")
        if self._memory and hasattr(self._memory, "flush"):
            try:
                await self._memory.flush()
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[EWA] flush error: {exc}")
        if self._chrona:
            self._chrona.unregister_pulse_handler(self._on_chrono_pulse)

        current_task = asyncio.current_task()
        for task in list(self._tasks):
            if task is current_task:
                continue
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()
        print(f"✅ EWA: session {self.session_id} archived")

    async def _save_yaml(self, payload: Dict[str, Any], suffix: str) -> None:
        os.makedirs("EvoMemory/ChronoSessions", exist_ok=True)
        path = f"EvoMemory/ChronoSessions/{self.session_id}_{suffix}.yaml"
        try:
            if yaml is None:
                import json

                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as handle:
                    yaml.dump(payload, handle, allow_unicode=True)
            print(f"📦 EWA: saved {path}")
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EWA] save yaml error: {exc}")


async def create_ewa_watcher(session_id: str, project: str, duration: str = "40m") -> EWAWatcher:
    from apps.core.memory.memory_manager import Memory

    watcher = EWAWatcher(session_id, duration)
    await watcher.start(Memory.for_project(project))
    return watcher
"""Event Watch & Archive (EWA) watcher utilities."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, List, Optional


PulseHandler = Callable[[datetime], None]


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


class Chrona:
    """Light-weight scheduler abstraction used to broadcast chrono pulses.

    The production version of the platform exposes a global ``chrona`` singleton
    that notifies registered handlers about heartbeat ticks.  For the test
    environment we keep the implementation deliberately small yet deterministic
    so we can reason about handler registrations during a session lifecycle.
    """

    def __init__(self) -> None:
        self._handlers: List[PulseHandler] = []

    def register_pulse_handler(self, handler: PulseHandler) -> None:
        """Register a pulse handler if it hasn't been registered yet."""

        if handler not in self._handlers:
            self._handlers.append(handler)

    def unregister_pulse_handler(self, handler: PulseHandler) -> None:
        """Remove a previously registered pulse handler."""

        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit_pulse(self, when: Optional[datetime] = None) -> None:
        """Fire a chrono pulse to all registered handlers."""

        timestamp = when or _utcnow()
        for handler in list(self._handlers):
            handler(timestamp)

    @property
    def handler_count(self) -> int:
        """Return the amount of currently registered handlers."""

        return len(self._handlers)


chrona = Chrona()


@dataclass
class EWAPulse:
    """Represents a single observation captured by the watcher."""

    payload: Any
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class EWASessionArchive:
    """Snapshot of all observations captured during a session."""

    session_id: str
    started_at: datetime
    ended_at: datetime
    pulses: List[EWAPulse]


class EWAWatcher:
    """Session watcher that archives observation bursts on chrono pulses."""

    def __init__(
        self,
        session_id: str,
        *,
        chrona_instance: Chrona | None = None,
    ) -> None:
        self.session_id = session_id
        self._chrona = chrona_instance or chrona
        self._chrona.register_pulse_handler(self._on_chrono_pulse)
        self._chrona_registered = True

        self._active = True
        self._session_active = False
        self._started_at: datetime | None = None
        self._pulses: List[EWAPulse] = []
        self._archive: List[EWASessionArchive] = []
        self._tasks: set[asyncio.Task[Any]] = set()
        self._session_timer: asyncio.Task[Any] | None = None

    def __enter__(self) -> "EWAWatcher":
        raise RuntimeError("Use 'async with' to manage an EWAWatcher instance")

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        raise RuntimeError("Use 'async with' to manage an EWAWatcher instance")

    async def __aenter__(self) -> "EWAWatcher":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.teardown()

    @property
    def chrona(self) -> Chrona:
        """Expose the chrona instance for testing/inspection."""

        return self._chrona

    @property
    def archive(self) -> List[EWASessionArchive]:
        """Return a copy of the archived session snapshots."""

        return list(self._archive)

    async def start(self) -> None:
        """Begin a new watcher session."""

        if self._session_active:
            raise RuntimeError("Watcher session already active")
        self._started_at = _utcnow()
        self._session_active = True
        self._active = True
        loop = asyncio.get_running_loop()
        if self._session_timer is None:
            self._session_timer = loop.create_task(
                self._monitor_flow(),
                name=f"EWAWatcher[{self.session_id}].monitor_flow",
            )
            self._track_task(self._session_timer)

    def record(self, payload: Any) -> None:
        """Record a payload for the active session."""

        if not self._session_active:
            raise RuntimeError("Cannot record without an active session")
        self._pulses.append(EWAPulse(payload=payload))

    async def teardown(self) -> None:
        """Public shutdown entry point."""

        if not self._session_active:
            self._active = False
            await self._cancel_background_tasks()
            self._unregister_from_chrona()
            return
        await self._finalize()

    def flush(self) -> None:
        """Manually trigger a flush of the current session payloads."""

        if not self._session_active:
            return
        self._archive_session()
        self._flush_buffers()

    def _on_chrono_pulse(self, _: datetime) -> None:
        if not self._session_active:
            return
        if not self._pulses:
            return
        self._archive_session()
        self._flush_buffers()

    def _archive_session(self) -> None:
        if not self._pulses or self._started_at is None:
            return
        snapshot = EWASessionArchive(
            session_id=self.session_id,
            started_at=self._started_at,
            ended_at=_utcnow(),
            pulses=list(self._pulses),
        )
        self._archive.append(snapshot)

    def _flush_buffers(self) -> None:
        self._pulses.clear()

    async def _finalize(self) -> None:
        self._archive_session()
        self._flush_buffers()
        self._session_active = False
        self._active = False
        await self._cancel_background_tasks()
        self._unregister_from_chrona()

    def _unregister_from_chrona(self) -> None:
        if not self._chrona_registered:
            return
        self._chrona.unregister_pulse_handler(self._on_chrono_pulse)
        self._chrona_registered = False

    async def _monitor_flow(self) -> None:
        """Background coroutine that stays alive while the watcher is active."""

        task = asyncio.current_task()
        try:
            while self._active:
                await asyncio.sleep(0.1)
        finally:
            if task is not None:
                self._tasks.discard(task)

    def _track_task(self, task: asyncio.Task[Any]) -> None:
        self._tasks.add(task)
        task.add_done_callback(lambda finished: self._tasks.discard(finished))

    async def _cancel_background_tasks(self) -> None:
        if not self._tasks:
            return

        current = asyncio.current_task()
        tasks_to_await: list[asyncio.Task[Any]] = []

        for task in list(self._tasks):
            if task is current:
                continue
            if task is self._session_timer:
                continue
            task.cancel()
            tasks_to_await.append(task)

        for task in tasks_to_await:
            with suppress(asyncio.CancelledError):
                await task
            self._tasks.discard(task)

        if self._session_timer is not None and self._session_timer is not current:
            with suppress(asyncio.CancelledError):
                await self._session_timer
            self._tasks.discard(self._session_timer)

        self._session_timer = None

    @property
    def background_task_count(self) -> int:
        """Expose the number of tracked background tasks still alive."""

        return sum(1 for task in self._tasks if not task.done())


__all__ = [
    "Chrona",
    "EWAPulse",
    "EWASessionArchive",
    "EWAWatcher",
    "chrona",
]
