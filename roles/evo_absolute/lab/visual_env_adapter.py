"""Visual Studio / EvoFinArt laboratory adapter for EvoAbsolute Ω."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:  # PyYAML is preferred but optional during CI probes
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback when dependency missing
    yaml = None

from . import EVOFINART_ROOT

LOG_ROOT = Path("logs") / "evo_absolute"


@dataclass
class LinkEvent:
    """Represents a synchronisation event emitted by EvoAbsolute."""

    channel: str
    project: str
    status: str
    details: Dict[str, Any]
    emitted_at: datetime

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["emitted_at"] = self.emitted_at.isoformat()
        return payload


class VisualEnvAdapter:
    """Coordinator that links EvoPyramid with the EvoFinArt laboratory."""

    def __init__(self, project_root: Optional[Path] = None, log_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(os.getcwd()).resolve()
        self.log_root = (log_root or LOG_ROOT).resolve()
        self.sync_log = self.log_root / "sync.log"
        self.bridge_log = self.log_root / "finart_bridge.log"
        self.reflection_path = self.log_root / "reflection.json"
        self.log_root.mkdir(parents=True, exist_ok=True)
        self._touch_logs()

    def _touch_logs(self) -> None:
        for log_path in (self.sync_log, self.bridge_log):
            log_path.touch(exist_ok=True)
        if not self.reflection_path.exists():
            self.reflection_path.write_text("{}\n", encoding="utf-8")

    def load_finart_manifest(self) -> Dict[str, Any]:
        manifest_path = EVOFINART_ROOT / "finart_manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing EvoFinArt manifest at {manifest_path}")
        text = manifest_path.read_text(encoding="utf-8")
        if yaml is None:
            return {"raw": text}
        return yaml.safe_load(text) or {}

    def emit_link_event(self, status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = self.load_finart_manifest()
        event = LinkEvent(
            channel="EvoAbsolute.link_event",
            project=manifest.get("project", {}).get("name", "EvoFinArt"),
            status=status,
            details=details or {},
            emitted_at=datetime.now(timezone.utc),
        )
        payload = event.to_payload()

        with self.sync_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

        self._relay_to_trinity(payload)
        self._update_reflection(payload)
        return payload

    def _relay_to_trinity(self, payload: Dict[str, Any]) -> None:
        try:
            from apps.core.observers.trinity_observer import TrinityObserver
        except Exception:  # pragma: no cover - Trinity is optional during tests
            return

        observer = TrinityObserver(system_name="EvoPyramid:EvoAbsolute")
        try:
            observer.record_evoabsolute_link_event(payload)
        except AttributeError:
            # Maintain compatibility if TrinityObserver lacks the new hook.
            observer.register_external_event("evo_absolute.link", payload)

    def _update_reflection(self, payload: Dict[str, Any]) -> None:
        reflection = {
            "last_sync": payload["emitted_at"],
            "status": payload["status"],
            "details": payload["details"],
        }
        self.reflection_path.write_text(json.dumps(reflection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def summarize_lab(self) -> Dict[str, Any]:
        manifest = self.load_finart_manifest()
        summary = {
            "lab_root": str(EVOFINART_ROOT),
            "solutions": [str(path.name) for path in EVOFINART_ROOT.glob("*.sln")],
            "modules": sorted(path.name for path in EVOFINART_ROOT.glob("*.py")),
            "manifest": manifest,
        }
        with self.bridge_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"summary": summary, "ts": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False) + "\n")
        return summary

    def run_ci_probe(self) -> Dict[str, Any]:
        summary = self.summarize_lab()
        payload = self.emit_link_event(status="ci_probe", details={"summary": summary})
        return {"summary": summary, "event": payload}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoAbsolute Visual Environment Adapter")
    parser.add_argument("mode", choices=["status", "sync", "ci"], nargs="?", default="status")
    parser.add_argument("--project-root", dest="project_root", default=None, help="Optional project root for relative resolution")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    adapter = VisualEnvAdapter(project_root=Path(args.project_root).resolve() if args.project_root else None)

    if args.mode == "status":
        summary = adapter.summarize_lab()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.mode == "sync":
        payload = adapter.emit_link_event(status="manual_sync", details={"trigger": "manual"})
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:  # ci mode
        result = adapter.run_ci_probe()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
