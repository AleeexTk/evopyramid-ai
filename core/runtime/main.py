"""Unified runtime launcher for EvoPyramid environments."""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.core.context.environment_detector import detect_environment
from core.runtime.config import RuntimeConfig
from core.runtime.environment import RuntimeAdapter, RuntimeAdapterError
from core.runtime.termux_adapter import TermuxAdapter


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EvoPyramid runtime orchestrator")
    parser.add_argument("--environment", choices=["auto", "termux"], default="auto")
    parser.add_argument("--entry-point", help="Python module to execute", default=None)
    parser.add_argument("--entry-arg", action="append", default=[], help="Arguments passed to the entry module")
    parser.add_argument("--repo-dir", type=Path, help="Repository directory override")
    parser.add_argument("--repo-url", help="Repository URL override")
    parser.add_argument("--logs-dir", type=Path, help="Directory to store runtime logs")
    parser.add_argument("--git-remote", help="Git remote name", default=None)
    parser.add_argument("--git-branch", help="Git branch name", default=None)
    parser.add_argument("--python-bin", type=Path, help="Python interpreter path")
    parser.add_argument("--reset", action="store_true", help="Remove existing repository before syncing")
    parser.add_argument("--no-push", action="store_true", help="Skip pushing local changes")
    parser.add_argument("--no-safe-directory", action="store_true", help="Do not register git safe.directory")
    parser.add_argument("--migrate-from", action="append", default=[], type=Path, help="Legacy repository paths to migrate")
    parser.add_argument("--log-file", type=Path, help="Explicit log file path")
    return parser.parse_args(argv)


def build_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("EvoRuntime")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger


def determine_environment(requested: str) -> str:
    if requested != "auto":
        return requested
    snapshot = detect_environment()
    return snapshot.get("env_type", "desktop")


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    defaults = {}
    if args.repo_url:
        defaults["repo_url"] = args.repo_url
    if args.repo_dir:
        defaults["repo_dir"] = str(args.repo_dir)
    if args.logs_dir:
        defaults["logs_dir"] = str(args.logs_dir)
    if args.git_remote:
        defaults["git_remote"] = args.git_remote
    if args.git_branch:
        defaults["git_branch"] = args.git_branch
    if args.python_bin:
        defaults["python_bin"] = str(args.python_bin)
    if args.entry_point:
        defaults["entry_point"] = args.entry_point
    if args.entry_arg:
        defaults["entry_args"] = " ".join(args.entry_arg)
    if args.migrate_from:
        defaults["migrate_sources"] = ":".join(str(p) for p in args.migrate_from)
    defaults["reset_repository"] = "true" if args.reset else "false"
    defaults["push_changes"] = "false" if args.no_push else "true"
    defaults["auto_safe_directory"] = "false" if args.no_safe_directory else "true"
    config = RuntimeConfig.from_env(defaults=defaults)
    if args.entry_arg:
        config = config.with_overrides(entry_args=list(args.entry_arg))
    if args.migrate_from:
        config = config.with_overrides(migrate_sources=list(args.migrate_from))
    return config


def select_adapter(environment: str, config: RuntimeConfig, logger: logging.Logger) -> RuntimeAdapter:
    if environment == "termux":
        return TermuxAdapter(config, logger)
    raise RuntimeAdapterError(f"Unsupported environment: {environment}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    environment = determine_environment(args.environment)
    config = build_config(args)
    if not config.entry_point:
        config = config.with_overrides(entry_point="apps.core.trinity_observer")
    if not config.migrate_sources and environment == "termux":
        config = config.with_overrides(
            migrate_sources=[
                Path("/storage/emulated/0/EVO_LOCAL/evopyramid-ai"),
                Path("/sdcard/EVO_LOCAL/evopyramid-ai"),
            ]
        )

    log_path = args.log_file or (config.logs_dir / f"runtime-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.log")
    logger = build_logger(log_path)
    logger.info("Runtime initialising for environment=%s", environment)

    try:
        adapter = select_adapter(environment, config, logger)
    except RuntimeAdapterError as exc:
        logger.error("%s", exc)
        return 1

    try:
        adapter.run()
    except RuntimeAdapterError as exc:
        logger.error("Runtime orchestration failed: %s", exc)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled runtime error: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
