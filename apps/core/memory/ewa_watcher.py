"""Event Watch & Archive (EWA) watcher utilities."""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from apps.core.time.evo_chrona import chrona as global_chrona

PulseHandler = Callable[[datetime], Any]


@dataclass
class EWAPulse:
    """Represents a single observation captured by the watcher."""

    payload: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EWASessionArchive:
    """Snapshot of all observations captured during a session."""

    session_id: str
    started_at: datetime
    ended_at: datetime
    pulses: List[EWAPulse]


class Chrona:
    """Minimal chrono used by unit tests to simulate pulse delivery."""

    def __init__(self) -> None:
        self._handlers: List[PulseHandler] = []

    def register_pulse_handler(self, handler: PulseHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unregister_pulse_handler(self, handler: PulseHandler) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit_pulse(self, when: Optional[datetime] = None) -> None:
        timestamp = when or datetime.now(UTC)
        for handler in list(self._handlers):
            try:
                result = handler(timestamp)
                if asyncio.iscoroutine(result):
                    asyncio.get_running_loop().create_task(result)
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[Chrona] handler error: {exc}")

    @property
    def handler_count(self) -> int:
        return len(self._handlers)


class EWAWatcher:
    """Session watcher that archives observation bursts on chrono pulses."""

    def __init__(
        self,
        session_id: str,
        *,
        duration: str = "40m",
        mode: str = "session",
        chrona_instance: Any | None = None,
    ) -> None:
        self.session_id = session_id
        self.mode = mode
        self._chrona = chrona_instance or global_chrona
        self._chrona_registered = False
        if isinstance(self._chrona, Chrona):
            self._chrona_handler = self._handle_pulse_sync
        else:
            self._chrona_handler = self._handle_pulse_async

        self._duration = self._parse_duration(duration)
        self.monitor_interval = 0.1

        self._memory: Optional[Any] = None
        self._tasks: List[asyncio.Task[Any]] = []
        self._session_timer: asyncio.Task[Any] | None = None
        self._active = False
        self._session_active = False
        self._finalized = False

        self._started_at: datetime | None = None
        self._pending_payloads: List[Any] = []
        self._pulses: List[EWAPulse] = []
        self._archive: List[EWASessionArchive] = []

        self.events: List[Dict[str, Any]] = []
        self.current_flow_state: Dict[str, Any] = {
            "coherence": 0.5,
            "soul_resonance": 0.5,
            "density": "medium",
            "tempo": "stable",
        }
        self._register_with_chrona()

    async def start(self, memory: Optional[Any] = None) -> None:
        """Begin a new watcher session."""

        if self._session_active:
            raise RuntimeError("Watcher session already active")

        self._memory = memory
        self._session_active = True
        self._active = True
        self._finalized = False
        self._started_at = datetime.now(UTC)

        self._register_with_chrona()

        loop = asyncio.get_running_loop()
        monitor = loop.create_task(
            self._monitor_flow(), name=f"EWAWatcher[{self.session_id}].monitor_flow"
        )
        self._tasks.append(monitor)
        self._session_timer = loop.create_task(
            self._session_timer_loop(),
            name=f"EWAWatcher[{self.session_id}].session_timer",
        )

    async def __aenter__(self) -> "EWAWatcher":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.teardown()

    async def teardown(self) -> None:
        """Shut down the watcher and persist collected state."""

        if not self._session_active:
            await self._cancel_background_tasks()
            self._unregister_from_chrona()
            return
        await self._finalize()

    def capture_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a contextual event for the session."""

        self.events.append(
            {
                "type": event_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "data": data,
                "flow_state": dict(self.current_flow_state),
            }
        )

    def record(self, payload: Any) -> None:
        """Record a payload for the active session."""

        if not self._session_active:
            raise RuntimeError("Cannot record without an active session")
        self._pending_payloads.append(payload)

    def flush(self) -> None:
        """Force creation of a snapshot from pending payloads."""

        if not self._session_active:
            return
        if self._pending_payloads:
            for payload in self._pending_payloads:
                self._pulses.append(EWAPulse(payload=payload))
            self._pending_payloads.clear()
        if self._pulses:
            self._archive_session()
            self._pulses.clear()

    @property
    def archive(self) -> List[EWASessionArchive]:
        return list(self._archive)

    @property
    def background_task_count(self) -> int:
        return sum(1 for task in self._tasks if not task.done())

    def _register_with_chrona(self) -> None:
        if self._chrona_registered:
            return
        register = getattr(self._chrona, "register_pulse_handler", None)
        if register is None:
            raise AttributeError("Chrona instance does not support pulse handlers")
        register(self._chrona_handler)
        self._chrona_registered = True

    def _unregister_from_chrona(self) -> None:
        if not self._chrona_registered:
            return
        unregister = getattr(self._chrona, "unregister_pulse_handler", None)
        if unregister is not None:
            unregister(self._chrona_handler)
        self._chrona_registered = False

    def _handle_pulse_sync(self, pulse: Any) -> None:
        if isinstance(pulse, dict):
            timestamp = datetime.fromisoformat(pulse.get("timestamp", datetime.now().isoformat()))
        elif isinstance(pulse, datetime):
            timestamp = pulse
        else:
            timestamp = datetime.now(UTC)
        self._process_pulse(timestamp)

    async def _handle_pulse_async(self, pulse: Any) -> None:
        if isinstance(pulse, dict):
            timestamp = datetime.fromisoformat(pulse.get("timestamp", datetime.now().isoformat()))
        elif isinstance(pulse, datetime):
            timestamp = pulse
        else:
            timestamp = datetime.now(UTC)
        self._process_pulse(timestamp)

    def _process_pulse(self, timestamp: datetime) -> None:
        if not self._session_active:
            return
        if self._pending_payloads:
            for payload in self._pending_payloads:
                self._pulses.append(EWAPulse(payload=payload, timestamp=timestamp))
            self._pending_payloads.clear()
        if self._pulses:
            self._archive_session(timestamp)
            self._pulses.clear()

    async def _monitor_flow(self) -> None:
        try:
            while self._active:
                await asyncio.sleep(self.monitor_interval)
                if not self._active:
                    break
                try:
                    from apps.core.monitoring.flow_monitor import FlowMonitor

                    flow = FlowMonitor.get_current_flow()
                except Exception:
                    flow = {}
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
        except asyncio.CancelledError:
            raise

    async def _session_timer_loop(self) -> None:
        try:
            await asyncio.sleep(self._duration.total_seconds())
            await self._finalize()
        except asyncio.CancelledError:
            raise

    def _archive_session(self, timestamp: Optional[datetime] = None) -> None:
        if not self._pulses or self._started_at is None:
            return
        snapshot = EWASessionArchive(
            session_id=self.session_id,
            started_at=self._started_at,
            ended_at=timestamp or datetime.now(UTC),
            pulses=list(self._pulses),
        )
        self._archive.append(snapshot)

    async def _finalize(self) -> None:
        if self._finalized:
            return
        self.flush()
        self._session_active = False
        self._active = False
        self._finalized = True

        await self._cancel_background_tasks()
        self._unregister_from_chrona()

        await self._persist_session()
        await self._flush_memory()

    async def _cancel_background_tasks(self) -> None:
        if not self._tasks and self._session_timer is None:
            return

        current = asyncio.current_task()
        tasks_to_wait: List[asyncio.Task[Any]] = []
        for task in list(self._tasks):
            if task is current:
                continue
            task.cancel()
            tasks_to_wait.append(task)

        for task in tasks_to_wait:
            with suppress(asyncio.CancelledError):
                await task
            self._tasks.remove(task)

        if self._session_timer is not None and self._session_timer is not current:
            self._session_timer.cancel()
            with suppress(asyncio.CancelledError):
                await self._session_timer
        self._session_timer = None
        self._tasks.clear()

    async def _persist_session(self) -> None:
        if self._started_at is None:
            return
        payload = {
            "session_id": self.session_id,
            "mode": self.mode,
            "started_at": self._started_at.isoformat(),
            "ended_at": datetime.now(UTC).isoformat(),
            "events": self.events,
            "flow_state": self.current_flow_state,
            "archive_size": len(self._archive),
        }
        await self._save_yaml(payload, suffix="final")

    async def _flush_memory(self) -> None:
        if self._memory is None:
            return
        flush = getattr(self._memory, "flush", None)
        if flush is None:
            return
        try:
            result = flush()
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EWAWatcher] memory flush error: {exc}")

    async def _save_yaml(self, payload: Dict[str, Any], suffix: str) -> None:
        os.makedirs("EvoMemory/ChronoSessions", exist_ok=True)
        path = f"EvoMemory/ChronoSessions/{self.session_id}_{suffix}.yaml"
        try:
            if yaml is None:
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as handle:
                    yaml.dump(payload, handle, allow_unicode=True)
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[EWAWatcher] save yaml error: {exc}")

    @staticmethod
    def _parse_duration(raw: str) -> timedelta:
        cleaned = raw.strip().lower()
        if cleaned.endswith("m"):
            return timedelta(minutes=int(cleaned[:-1] or 0))
        if cleaned.endswith("h"):
            return timedelta(hours=int(cleaned[:-1] or 0))
        return timedelta(minutes=40)


async def create_ewa_watcher(
    session_id: str, project: str, duration: str = "40m"
) -> EWAWatcher:
    """Factory helper used by integration flows."""

    from apps.core.memory.memory_manager import Memory

    watcher = EWAWatcher(session_id, duration=duration, chrona_instance=global_chrona)
    await watcher.start(Memory.for_project(project))
    return watcher


chrona = global_chrona

__all__ = [
    "Chrona",
    "EWAWatcher",
    "EWAPulse",
    "EWASessionArchive",
    "create_ewa_watcher",
]
