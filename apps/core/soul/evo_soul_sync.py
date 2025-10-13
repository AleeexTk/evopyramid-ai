"""Soul synchronization utility for reflecting on Evo Container chronicles."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

CHRONICLE_DIR = Path("containers/evo_container/evo_link_bridge/narrator/logs/chronicles")
SOUL_LOG = Path("logs/soul_sync.log")


@dataclass(slots=True)
class ChronicleSnapshot:
    """A lightweight view on a chronicle artifact."""

    path: Path
    timestamp: datetime
    profile: str
    coherence: float
    ready: bool

    def as_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "profile": self.profile,
            "coherence": round(self.coherence, 3),
            "ready": self.ready,
        }


def _load_snapshot(path: Path) -> ChronicleSnapshot | None:
    with path.open("r", encoding="utf-8") as handle:
        header = handle.readline().strip()
    if not header:
        return None
    metadata = json.loads(header)
    timestamp = datetime.fromisoformat(str(metadata.get("timestamp")))
    profile = str(metadata.get("profile", "unknown"))
    coherence = float(metadata.get("coherence", 0.0))
    ready = bool(metadata.get("ready", False))
    return ChronicleSnapshot(
        path=path,
        timestamp=timestamp,
        profile=profile,
        coherence=coherence,
        ready=ready,
    )


def scan_chronicles(log_dir: Path = CHRONICLE_DIR) -> List[ChronicleSnapshot]:
    """Collect snapshots from available chronicles."""

    if not log_dir.exists():
        return []
    snapshots: List[ChronicleSnapshot] = []
    for item in sorted(log_dir.glob("evochronicle_*.txt")):
        snapshot = _load_snapshot(item)
        if snapshot is not None:
            snapshots.append(snapshot)
    return snapshots


def build_reflection(snapshots: Iterable[ChronicleSnapshot]) -> Dict[str, object]:
    """Generate an aggregate reflection payload from chronicle snapshots."""

    snapshots = list(snapshots)
    total = len(snapshots)
    average_coherence = (
        round(sum(snapshot.coherence for snapshot in snapshots) / total, 3)
        if snapshots
        else 0.0
    )
    readiness_ratio = (
        round(sum(1 for snapshot in snapshots if snapshot.ready) / total, 3)
        if snapshots
        else 0.0
    )

    now = datetime.now(timezone.utc)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "total_chronicles": total,
        "average_coherence": average_coherence,
        "readiness_ratio": readiness_ratio,
        "profiles_observed": sorted({snapshot.profile for snapshot in snapshots}),
        "recent": [snapshot.as_dict() for snapshot in snapshots[-5:]],
    }


def write_reflection(reflection: Dict[str, object], output_path: Path = SOUL_LOG) -> None:
    """Append the reflection payload to the soul synchronization log."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(reflection, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Evo soul synchronization pass.")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=CHRONICLE_DIR,
        help="Directory containing chronicle logs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SOUL_LOG,
        help="Path for the soul reflection log.",
    )
    args = parser.parse_args()

    snapshots = scan_chronicles(args.log_dir)
    reflection = build_reflection(snapshots)
    write_reflection(reflection, args.output)
    print(json.dumps(reflection, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
