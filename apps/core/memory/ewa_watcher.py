import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
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

        chrona.register_pulse_handler(self._on_chrono_pulse)
        self._tasks: List[asyncio.Task] = []
        self._memory = None
        self.monitor_interval = 30.0

    def _parse_duration(self, raw: str) -> timedelta:
        raw = raw.strip().lower()
        if raw.endswith("m"):
            return timedelta(minutes=int(raw[:-1] or 0))
        if raw.endswith("h"):
            return timedelta(hours=int(raw[:-1] or 0))
        return timedelta(minutes=40)

    async def start(self, memory) -> None:
        self._memory = memory
        print(f"🕰 EWA: session {self.session_id} for {self.duration}")
        self._tasks = [
            asyncio.create_task(self._monitor_flow()),
            asyncio.create_task(self._session_timer()),
        ]

    async def _on_chrono_pulse(self, pulse: Dict[str, Any]) -> None:
        remaining = self.end_time - datetime.utcnow()
        if remaining < self.duration * 0.25:
            if self.current_flow_state.get("coherence", 0.0) > 0.6:
                await self._autosave("session_nearing_end")

    async def _monitor_flow(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.monitor_interval)
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
