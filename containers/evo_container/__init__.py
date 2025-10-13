"""Evo Container package.

This namespace exposes the high-level primitives that orchestrate the
self-processing pipelines used across EvoPyramid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable


@dataclass
class PipelineContext:
    """Mutable container shared across pipeline stages.

    Attributes
    ----------
    profile:
        Active Evo persona profile identifier.
    link:
        Optional external reference imported into memory.
    manifest_path:
        Path to the manifest currently orchestrating execution.
    state:
        Arbitrary state accumulated by the pipeline.
    timeline:
        Ordered sequence of human-readable events for chronicle synthesis.
    metadata:
        Free-form metadata exposed to downstream systems.
    """

    profile: str | None = None
    link: str | None = None
    manifest_path: Path | None = None
    state: Dict[str, Any] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def log_event(self, channel: str, message: str, **payload: Any) -> None:
        """Record a structured event in the pipeline timeline."""

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": channel,
            "message": message,
        }
        if payload:
            entry["payload"] = payload
        self.timeline.append(entry)

    def update_state(self, key: str, value: Any) -> None:
        """Persist a value under ``state`` and mirror it in metadata if requested."""

        self.state[key] = value

    def extend_metadata(self, **items: Any) -> None:
        """Merge new metadata attributes into the context."""

        self.metadata.update(items)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable snapshot of the execution context."""

        return {
            "profile": self.profile,
            "link": self.link,
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "state": self.state,
            "timeline": self.timeline,
            "metadata": self.metadata,
        }


def ensure_directory(path: Path | str) -> Path:
    """Ensure that a directory exists and return it."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def iter_events(timeline: Iterable[Dict[str, Any]]) -> Iterable[str]:
    """Yield formatted narrative fragments from raw timeline events."""

    for event in timeline:
        timestamp = event.get("timestamp", "?")
        channel = event.get("channel", "event")
        message = event.get("message", "")
        payload = event.get("payload")
        fragment = f"[{timestamp}] ({channel}) {message}"
        if payload:
            fragment += f" :: {payload}"
        yield fragment
