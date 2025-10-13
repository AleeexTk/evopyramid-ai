#!/usr/bin/env python3
"""Utility script for executing EvoContainer manifests."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from containers.evo_container.cli import DEFAULT_MANIFEST_PATH, format_summary, run_pipeline


def _resolve_manifest(path: str | None) -> Path:
    if path is None:
        return DEFAULT_MANIFEST_PATH
    return Path(path).expanduser().resolve()


def command_run_pipeline(args: argparse.Namespace) -> int:
    manifest_path = _resolve_manifest(args.manifest)
    context = run_pipeline(
        args.pipeline,
        link=args.link,
        profile=args.profile,
        manifest_path=manifest_path,
    )
    print(format_summary(context))
    return 0


def command_show_manifest(args: argparse.Namespace) -> int:
    manifest_path = _resolve_manifest(args.manifest)
    data: Any = manifest_path.read_text(encoding="utf-8")
    print(data)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoContainer manifest runner")
    parser.add_argument("--manifest", help="Path to a manifest file", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-pipeline", help="Execute a manifest pipeline")
    run_parser.add_argument("pipeline", help="Name of the pipeline to run")
    run_parser.add_argument("--link", help="External link or artefact to ingest", default=None)
    run_parser.add_argument("--profile", help="Profile name guiding the run", default=None)
    run_parser.set_defaults(func=command_run_pipeline)

    show_parser = subparsers.add_parser("show-manifest", help="Print manifest contents")
    show_parser.set_defaults(func=command_show_manifest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "func", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
