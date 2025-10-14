"""Response schema helpers for EvoPyramid API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class ReviewInsight:
    """Structured insight produced by Codex review."""

    severity: str
    message: str
    file_path: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class SimulationResult:
    """Result skeleton for FinArt trade simulations."""

    strategy: str
    horizon_minutes: int
    expected_value: float
    metadata: Dict[str, str] = field(default_factory=dict)
