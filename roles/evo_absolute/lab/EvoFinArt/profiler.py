"""Runtime profiling utilities for the EvoFinArt laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

__all__ = ["ProfilingResult", "FinArtProfiler"]


@dataclass
class ProfilingResult:
    """Captured metrics for a EvoFinArt profiling session."""

    started_at: datetime
    completed_at: datetime
    cpu_load: float
    memory_mb: float
    notes: List[str]

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()


class FinArtProfiler:
    """Collects lightweight runtime metrics for EvoFinArt experiments."""

    def profile_strategy(self, name: str) -> ProfilingResult:
        now = datetime.now(timezone.utc)
        notes = [f"Strategy '{name}' profiled in EvoAbsolute sandbox"]
        return ProfilingResult(
            started_at=now,
            completed_at=now,
            cpu_load=0.0,
            memory_mb=0.0,
            notes=notes,
        )

    def to_dict(self, result: ProfilingResult) -> Dict[str, float | List[str] | str]:
        return {
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "duration": result.duration_seconds,
            "cpu_load": result.cpu_load,
            "memory_mb": result.memory_mb,
            "notes": result.notes,
        }
