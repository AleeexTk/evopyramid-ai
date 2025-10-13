"""Evo Soul Sync – reflective telemetry engine."""

from __future__ import annotations

import argparse
import json
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
