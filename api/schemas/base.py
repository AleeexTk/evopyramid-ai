"""Core data structures for EvoPyramid API payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class DiffSnippet:
    """Minimal representation of a diff hunk under review."""

    file_path: str
    text: str


@dataclass(slots=True)
class CodeReviewRequest:
    """Payload for Codex evaluation requests."""

    author: str
    diff_snippets: List[DiffSnippet] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass(slots=True)
class TradeSimulationRequest:
    """Input contract for FinArt trade simulations."""

    strategy_name: str
    position_size: float
    expected_edge: float
    horizon_minutes: int
    risk_limit: float


@dataclass(slots=True)
class KairosMoment:
    """Semantic snapshot stored in EvoMemory."""

    identifier: str
    narrative: str
    resonance: str
    importance: int
    timestamp: datetime
