"""Shared dataclasses and protocols for context analysis components."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class IntentResult:
    """Intent detection result."""

    urgency: float
    type: str
    confidence: float

    def to_dict(self) -> Dict[str, float | str]:
        """Convert the dataclass to a dictionary."""

        return asdict(self)


@dataclass
class AffectResult:
    """Affective analysis result."""

    soul_resonance: float
    emotion: str
    intensity: float

    def to_dict(self) -> Dict[str, float | str]:
        """Convert the dataclass to a dictionary."""

        return asdict(self)


@dataclass
class MemoryResult:
    """Memory lookup result."""

    has_strong_links: bool
    fragments: List[str]
    relevance_score: float
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary."""

        return asdict(self)


class MemoryLedgerProtocol(Protocol):
    """Protocol describing the memory ledger behaviour."""

    async def find_related_fragments(
        self,
        query: str,
        threshold: float = 0.85,
    ) -> MemoryResult:
        """Return related fragments for the provided query."""

