#!/usr/bin/env python3
"""Utility to inspect and execute Evo manifest pipelines."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "containers" / "evo_container" / "manifests" / "EVO_CONTAINER_MANIFEST.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_entrypoint(entrypoint: str) -> Callable[..., Any]:
    if ":" not in entrypoint:
        raise ValueError("entrypoint must be in the form 'module:function'")
    module_name, func_name = entrypoint.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    return func


def show_pipelines(manifest: Dict[str, Any]) -> None:
    pipelines = manifest.get("pipelines", {})
    for name, payload in pipelines.items():
        summary = payload.get("summary", "No summary provided")
        print(f"- {name}: {summary}")


def run_pipeline_command(manifest: Dict[str, Any], name: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    pipelines = manifest.get("pipelines", {})
    if name not in pipelines:
        raise KeyError(f"Pipeline '{name}' is not defined in the manifest")
    entrypoint = pipelines[name].get("entrypoint")
    if not entrypoint:
        raise ValueError(f"Pipeline '{name}' is missing an entrypoint definition")
    func = resolve_entrypoint(entrypoint)
    return func(name, initial_state)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evo manifest pipeline runner")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to the manifest YAML file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show-pipelines", help="List available pipelines")
    show_parser.set_defaults(handler=_handle_show_pipelines)

    run_parser = subparsers.add_parser("run-pipeline", help="Execute a pipeline by name")
    run_parser.add_argument("name", help="Pipeline name")
    run_parser.add_argument("--link", required=True, help="Link payload for intake stage")
    run_parser.add_argument("--profile", required=True, help="Profile to adapt the pipeline for")
    run_parser.set_defaults(handler=_handle_run_pipeline)

    return parser


def _handle_show_pipelines(args: argparse.Namespace, manifest: Dict[str, Any]) -> None:
    show_pipelines(manifest)


def _handle_run_pipeline(args: argparse.Namespace, manifest: Dict[str, Any]) -> None:
    state = {"link": args.link, "profile": args.profile}
    result = run_pipeline_command(manifest, args.name, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    args.handler(args, manifest)


if __name__ == "__main__":
    main()
"""Universal runner for Evo Container manifests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from containers.evo_container import cli  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return cli.cli(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
