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
