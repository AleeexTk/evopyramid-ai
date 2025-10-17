"""Configuration helpers for EvoPyramid runtime environments."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


@dataclass
class RuntimeConfig:
    """Runtime configuration values shared across adapters."""

    repo_url: str
    repo_dir: Path
    logs_dir: Path
    entry_point: Optional[str] = None
    entry_args: Sequence[str] = field(default_factory=list)
    python_bin: Optional[Path] = None
    git_remote: str = "origin"
    git_branch: str = "main"
    auto_safe_directory: bool = True
    reset_repository: bool = False
    migrate_sources: Sequence[Path] = field(default_factory=list)
    push_changes: bool = True
    extra_env: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(
        cls,
        defaults: Optional[Mapping[str, str]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> "RuntimeConfig":
        """Construct configuration using environment variables."""

        env_map: Mapping[str, str] = env or os.environ
        base: dict[str, str] = {}
        if defaults:
            base.update(defaults)

        if "EVO_RUNTIME_CONFIG" in env_map:
            payload = _load_external_config(Path(env_map["EVO_RUNTIME_CONFIG"]))
            base.update(payload)

        prefix = "EVO_RUNTIME_"
        for key, value in env_map.items():
            if not key.startswith(prefix):
                continue
            if key.startswith("EVO_RUNTIME_EXTRA_"):
                continue
            base[key[len(prefix):].lower()] = value

        repo_dir = Path(base.get("repo_dir") or env_map.get("EVO_PARENT_DIR") or Path.home() / "evopyramid-ai")
        logs_dir = Path(base.get("logs_dir") or repo_dir.parent / "logs" / "runtime")

        migrate_sources = _parse_path_sequence(base.get("migrate_sources"))
        entry_point = base.get("entry_point")
        python_bin = Path(base["python_bin"]) if base.get("python_bin") else None
        entry_args = _parse_arg_list(base.get("entry_args"))

        config = cls(
            repo_url=base.get("repo_url", "https://github.com/AleeexTk/evopyramid-ai.git"),
            repo_dir=repo_dir,
            logs_dir=logs_dir,
            entry_point=entry_point,
            entry_args=entry_args,
            python_bin=python_bin,
            git_remote=base.get("git_remote", "origin"),
            git_branch=base.get("git_branch", "main"),
            auto_safe_directory=_to_bool(base.get("auto_safe_directory", "true")),
            reset_repository=_to_bool(base.get("reset_repository", base.get("reset", "false"))),
            migrate_sources=migrate_sources,
            push_changes=_to_bool(base.get("push_changes", "true")),
            extra_env=_extract_extra_env(env_map),
        )
        return config

    def with_overrides(self, **kwargs: object) -> "RuntimeConfig":
        """Return a mutated copy of the configuration."""

        data = self.__dict__.copy()
        data.update(kwargs)
        data["migrate_sources"] = [Path(p) for p in data.get("migrate_sources", [])]
        data["entry_args"] = list(data.get("entry_args", []))
        if data.get("python_bin") and not isinstance(data["python_bin"], Path):
            data["python_bin"] = Path(data["python_bin"])
        data["repo_dir"] = Path(data["repo_dir"])
        data["logs_dir"] = Path(data["logs_dir"])
        return RuntimeConfig(**data)


def _load_external_config(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Runtime config file not found: {path}")

    text = path.read_text(encoding="utf-8")
    payload: dict[str, str]
    if path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("pyyaml not installed; cannot load YAML runtime config")
        data = yaml.safe_load(text) or {}
        payload = {str(key): str(value) for key, value in data.items()}
    else:
        data = json.loads(text)
        payload = {str(key): str(value) for key, value in data.items()}
    return payload


def _parse_path_sequence(raw: Optional[str]) -> Sequence[Path]:
    if not raw:
        return []
    parts = [segment.strip() for segment in raw.replace(";", ":").split(":")]
    return [Path(part) for part in parts if part]


def _parse_arg_list(raw: Optional[str]) -> Sequence[str]:
    if not raw:
        return []
    return [segment for segment in raw.strip().split() if segment]


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _extract_extra_env(env_map: Mapping[str, str]) -> Mapping[str, str]:
    prefix = "EVO_RUNTIME_EXTRA_"
    return {k[len(prefix):]: v for k, v in env_map.items() if k.startswith(prefix)}


__all__ = ["RuntimeConfig"]
