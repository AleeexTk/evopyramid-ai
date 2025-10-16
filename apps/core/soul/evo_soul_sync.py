"""Soul synchronization utility for reflecting on Evo Container chronicles."""
"""Evo Soul Sync – reflective telemetry engine."""

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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "containers" / "evo_container" / "manifests" / "EVO_CONTAINER_MANIFEST.yaml"
SOUL_LOG = ROOT / "logs" / "soul_sync.log"


class SoulSyncReport(dict):
    """Structured report describing the internal reflective state."""

    def to_json(self) -> str:
        return json.dumps(self, indent=2, ensure_ascii=False)


def load_manifest(path: Path | str | None = None) -> Dict[str, Any]:
    manifest_path = Path(path or DEFAULT_MANIFEST)
    with manifest_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def synthesise_report(manifest: Dict[str, Any], profile: str | None = None) -> SoulSyncReport:
    metadata = manifest.get("metadata", {})
    modules = manifest.get("modules", {})
    pipelines = manifest.get("pipelines", {})

    report: SoulSyncReport = SoulSyncReport(
        timestamp=datetime.utcnow().isoformat() + "Z",
        persona=profile,
        manifest_id=metadata.get("id"),
        phase_focus=metadata.get("roadmap", [])[-1] if metadata.get("roadmap") else None,
        module_count=len(modules),
        pipeline_keys=list(pipelines.keys()),
        observers=[module for module, data in modules.items() if data.get("role", "").endswith("observer")],
    )

    report["dependencies"] = {
        module: modules[module].get("depends_on", [])
        for module in modules
        if modules[module].get("depends_on")
    }
    report["soul_sync"] = modules.get("evo_soul_sync", {})
    return report


def persist_report(report: SoulSyncReport, path: Path = SOUL_LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(report.to_json())
        handle.write("\n")


def cli(argv: list[str] | None = None) -> SoulSyncReport:
    parser = argparse.ArgumentParser(description="Emit a soul sync reflection report")
    parser.add_argument("--manifest", help="Path to a manifest with the evo_soul_sync module")
    parser.add_argument("--profile", help="Persona profile activating the reflection")
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    report = synthesise_report(manifest, profile=args.profile)
    persist_report(report)
    print(report.to_json())
    return report


if __name__ == "__main__":  # pragma: no cover
    cli()
