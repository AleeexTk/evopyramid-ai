"""Расширенный Trinity Observer для мониторинга мультиагентной системы."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

try:  # Runtime optional dependency: EvoLocalContext
    from apps.core.context import analyze_device, detect_environment
except Exception:  # pragma: no cover - graceful fallback
    def detect_environment() -> Dict[str, Any]:  # type: ignore
        return {"env_type": "unknown"}

    def analyze_device() -> Dict[str, Any]:  # type: ignore
        return {}


@dataclass
class _TrinityState:
    total_observations: int = 0
    insight_peaks: int = 0
    active_agents: int = 0
    temporal_coherence: float = 0.75
    current_phase: str = "stability"
    observer_mode: str = "guardian"
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class TrinityObserver:
    """Собирает телеметрию, совместимую с API и бенчмарками."""

    def __init__(self) -> None:
        self._state = _TrinityState()
        self._environment = detect_environment()
        self._device_metrics = analyze_device()

    async def get_current_state(self) -> Dict[str, Any]:
        async with self._state.lock:
            timestamp = datetime.now(timezone.utc).isoformat()
            return {
                "timestamp": timestamp,
                "environment": self._environment,
                "device": self._device_metrics,
                "observer_mode": self._state.observer_mode,
                "system_state": {
                    "temporal_coherence": round(self._state.temporal_coherence, 3),
                    "current_phase": self._state.current_phase,
                },
                "statistics": {
                    "total_observations": self._state.total_observations,
                    "insight_peaks": self._state.insight_peaks,
                    "active_agents": self._state.active_agents,
                },
            }

    async def record_interaction(self, node: str, trace_id: str) -> None:
        del trace_id
        async with self._state.lock:
            self._state.total_observations += 1
            if node == "soul":
                self._state.active_agents = max(1, self._state.active_agents)
            else:
                self._state.active_agents = max(1, self._state.active_agents)
            if random.random() > 0.7:
                self._state.insight_peaks += 1
            self._state.temporal_coherence = min(
                0.99, self._state.temporal_coherence + 0.01
            )
            if self._state.temporal_coherence > 0.85:
                self._state.current_phase = "peak_consciousness"

    async def heartbeat(self) -> None:
        async with self._state.lock:
            self._state.temporal_coherence = max(0.6, self._state.temporal_coherence - 0.02)
            self._state.active_agents = max(0, self._state.active_agents - 1)


trinity_observer = TrinityObserver()

__all__ = ["TrinityObserver", "trinity_observer"]
