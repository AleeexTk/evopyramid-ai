"""Event Watch & Archive (EWA) watcher utilities."""

from __future__ import annotations

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

        self._active = False
        self._started_at: datetime | None = None
        self._pulses: List[EWAPulse] = []
        self._archive: List[EWASessionArchive] = []

    def __enter__(self) -> "EWAWatcher":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.teardown()

    @property
    def chrona(self) -> Chrona:
        """Expose the chrona instance for testing/inspection."""

        return self._chrona

    @property
    def archive(self) -> List[EWASessionArchive]:
        """Return a copy of the archived session snapshots."""

        return list(self._archive)

    def start(self) -> None:
        """Begin a new watcher session."""

        if self._active:
            raise RuntimeError("Watcher session already active")
        self._started_at = _utcnow()
        self._active = True

    def record(self, payload: Any) -> None:
        """Record a payload for the active session."""

        if not self._active:
            raise RuntimeError("Cannot record without an active session")
        self._pulses.append(EWAPulse(payload=payload))

    def teardown(self) -> None:
        """Public shutdown entry point."""

        if not self._active:
            self._unregister_from_chrona()
            return
        self._finalize()

    def flush(self) -> None:
        """Manually trigger a flush of the current session payloads."""

        if not self._active:
            return
        self._archive_session()
        self._flush_buffers()

    def _on_chrono_pulse(self, _: datetime) -> None:
        if not self._active:
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

    def _finalize(self) -> None:
        self._archive_session()
        self._flush_buffers()
        self._active = False
        self._unregister_from_chrona()

    def _unregister_from_chrona(self) -> None:
        if not self._chrona_registered:
            return
        self._chrona.unregister_pulse_handler(self._on_chrono_pulse)
        self._chrona_registered = False


__all__ = [
    "Chrona",
    "EWAPulse",
    "EWASessionArchive",
    "EWAWatcher",
    "chrona",
]
