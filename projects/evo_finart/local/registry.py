"""Registry primitives for EvoFinArt local integration states."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

_DEFAULT_SEGMENTS: Mapping[str, str] = {
    "channels": "channels",
    "triggers": "triggers",
    "meta_quotas": "meta_quotas",
    "algo_trading": "algo_trading",
    "notion": "notion",
    "mail_sync": "mail_sync",
    "logs": "logs",
}


@dataclass(slots=True)
class LocalIntegrationSpace:
    """Describes the Local/ workspace dedicated to EvoAbsolute automation."""

    root: Path
    segments: Mapping[str, Path]

    def ensure(self) -> None:
        """Ensure that all dynamic integration directories exist."""

        for path in self.segments.values():
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, str]:
        """Serialize the workspace to plain paths for downstream tooling."""

        return {
            "root": str(self.root),
            **{name: str(path) for name, path in self.segments.items()},
        }

    def describe(self) -> str:
        """Return a human-readable overview of the workspace layout."""

        parts = [f"root={self.root}"]
        for name, path in self.segments.items():
            parts.append(f"{name}={path}")
        return "; ".join(parts)


def initialize_local_space(root: Path | str | None = None, *, ensure: bool = True) -> LocalIntegrationSpace:
    """Instantiate a :class:`LocalIntegrationSpace` anchored to ``Local/``."""

    if root is None:
        resolved_root = Path(__file__).resolve().parent
    else:
        resolved_root = Path(root).expanduser().resolve()

    segments = {name: resolved_root / relative for name, relative in _DEFAULT_SEGMENTS.items()}
    workspace = LocalIntegrationSpace(root=resolved_root, segments=segments)

    if ensure:
        workspace.ensure()

    return workspace
