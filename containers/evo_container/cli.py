"""Command utilities for the EvoContainer prototype."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional

import yaml

from . import PipelineStep, load_step_callable

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent / "manifests" / "EVO_CONTAINER_MANIFEST.yaml"


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the EvoContainer manifest as a Python dictionary."""

    path = Path(manifest_path) if manifest_path is not None else DEFAULT_MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run_pipeline(
    name: str,
    *,
    link: Optional[str] = None,
    profile: Optional[str] = None,
    manifest_path: Optional[Path] = None,
) -> MutableMapping[str, Any]:
    """Execute a named pipeline declared in the manifest."""

    manifest = load_manifest(manifest_path)
    pipelines = manifest.get("pipelines", {})
    if name not in pipelines:
        raise KeyError(f"Pipeline '{name}' is not defined in the manifest")

    pipeline: Dict[str, Any] = pipelines[name]
    steps: List[PipelineStep] = list(pipeline.get("steps", []))
    context: MutableMapping[str, Any] = {
        "link": link,
        "profile": profile,
        "events": [],
        "meta": {
            "pipeline": name,
            "manifest_version": manifest.get("version", "unknown"),
        },
    }

    for step in steps:
        callable_step = load_step_callable(step)
        callable_step(context)

    return context


def format_summary(context: MutableMapping[str, Any]) -> str:
    """Render a human-readable summary of the pipeline execution."""

    summary = context.get("summary", {})
    return json.dumps(summary, indent=2, ensure_ascii=False)


__all__ = ["DEFAULT_MANIFEST_PATH", "format_summary", "load_manifest", "run_pipeline"]
