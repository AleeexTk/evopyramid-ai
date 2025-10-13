"""Command helpers for Evo Container pipelines."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Mapping, MutableMapping

from . import adapt, analysis, harmonize, intake, integrate, syncer
from .evo_link_bridge.narrator import processor as narrator_processor

PipelineStep = Callable[[MutableMapping[str, object]], MutableMapping[str, object]]


PIPELINES: Dict[str, Iterable[PipelineStep]] = {
    "link_import_to_memory": (
        intake.collect_link,
        analysis.analyze_link,
        adapt.adapt_for_memory,
        integrate.integrate_payload,
        syncer.sync_memory,
        harmonize.harmonize_state,
        narrator_processor.create_chronicle,
    )
}


def run_pipeline(name: str, initial_state: Mapping[str, object]) -> Dict[str, object]:
    """Execute a named pipeline with the provided initial state."""

    if name not in PIPELINES:
        raise KeyError(f"Unknown pipeline '{name}'")

    state: MutableMapping[str, object] = dict(initial_state)
    for step in PIPELINES[name]:
        state = step(state)  # type: ignore[assignment]
    return dict(state)


__all__ = ["PIPELINES", "run_pipeline"]
"""Command line interface for Evo Container pipelines."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Dict

import yaml

from . import PipelineContext

DEFAULT_MANIFEST = Path(__file__).resolve().parent / "manifests" / "EVO_CONTAINER_MANIFEST.yaml"


class ManifestError(RuntimeError):
    """Raised when the manifest cannot be parsed or is inconsistent."""


def load_manifest(path: Path | str | None = None) -> Dict[str, Any]:
    """Load the container manifest from disk."""

    manifest_path = Path(path or DEFAULT_MANIFEST)
    if not manifest_path.exists():
        raise ManifestError(f"Manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict):
        raise ManifestError("Manifest must evaluate to a mapping")
    manifest.setdefault("modules", {})
    manifest.setdefault("pipelines", {})
    return manifest


def resolve_callable(path: str, default_attr: str = "run") -> Callable[[PipelineContext, Dict[str, Any]], Any]:
    """Import a callable from a module path."""

    module_name, _, attr = path.partition(":")
    attribute = attr or default_attr
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attribute)
    except AttributeError as exc:  # pragma: no cover - defensive guard
        raise ManifestError(f"Callable '{attribute}' not found in module '{module_name}'") from exc


def run_pipeline(name: str, context: PipelineContext, manifest: Dict[str, Any]) -> PipelineContext:
    """Execute the pipeline specified by *name* using the provided context."""

    pipeline = manifest.get("pipelines", {}).get(name)
    if not pipeline:
        raise ManifestError(f"Pipeline '{name}' is not defined in the manifest")

    steps = pipeline.get("steps", [])
    modules = manifest.get("modules", {})
    for index, step in enumerate(steps, start=1):
        module_key = step["module"]
        module_def = modules.get(module_key)
        if not module_def:
            raise ManifestError(f"Unknown module '{module_key}' referenced in pipeline '{name}'")

        path = module_def["path"]
        callable_path = path.replace("/", ".")
        if callable_path.endswith(".py"):
            callable_path = callable_path[:-3]
        entrypoint = step.get("entrypoint") or module_def.get("entrypoint", "run")
        runner = resolve_callable(f"{callable_path}:{entrypoint}")
        config = step.get("config", {})
        context.log_event(
            "pipeline",
            f"running step {index}: {module_key}",
            entrypoint=entrypoint,
            config=config,
        )
        result = runner(context, config)
        register_key = step.get("register") or module_def.get("register_key")
        if register_key:
            context.update_state(register_key, result)

    return context


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evo Container manifest runner")
    parser.add_argument("command", choices=["run-pipeline", "show"], help="Operation to perform")
    parser.add_argument("name", nargs="?", help="Pipeline name when running a pipeline")
    parser.add_argument("--manifest", dest="manifest", help="Path to an alternative manifest")
    parser.add_argument("--profile", dest="profile", help="Profile to activate")
    parser.add_argument("--link", dest="link", help="External link to ingest")
    parser.add_argument("--export", dest="export", help="Path to store the resulting context as JSON")

    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)

    if args.command == "show":
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    if not args.name:
        raise ManifestError("A pipeline name is required when running the manifest")

    context = PipelineContext(profile=args.profile, link=args.link, manifest_path=Path(args.manifest) if args.manifest else DEFAULT_MANIFEST)
    run_pipeline(args.name, context, manifest)

    if args.export:
        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with export_path.open("w", encoding="utf-8") as handle:
            json.dump(context.to_dict(), handle, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(context.to_dict(), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli())
