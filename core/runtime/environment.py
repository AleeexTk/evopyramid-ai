"""Base runtime adapter infrastructure."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from abc import ABC
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .config import RuntimeConfig


class RuntimeAdapterError(Exception):
    """Raised when runtime orchestration fails."""


class RuntimeAdapter(ABC):
    """Common interface for EvoPyramid runtime adapters."""

    def __init__(self, config: RuntimeConfig, logger: Optional[logging.Logger] = None) -> None:
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def prepare(self) -> None:
        """Prepare directories and perform migrations."""
        self.logger.debug("Preparing runtime environment")
        self._prepare_directories()
        self._migrate_if_needed()
        if self.config.reset_repository and self.config.repo_dir.exists():
            self.logger.info("Reset requested – removing %s", self.config.repo_dir)
            shutil.rmtree(self.config.repo_dir)
        self._ensure_repo_present()

    def _prepare_directories(self) -> None:
        self.logger.debug("Ensuring log directory %s", self.config.logs_dir)
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)

    def _migrate_if_needed(self) -> None:
        for source in self.config.migrate_sources:
            if not source.exists():
                continue
            try:
                if source.resolve() == self.config.repo_dir.resolve():
                    continue
            except OSError:
                if source == self.config.repo_dir:
                    continue
            self.logger.info("Migrating legacy repository from %s", source)
            self._relocate_repository(source, self.config.repo_dir)

    def _relocate_repository(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            self.logger.warning("Destination %s already exists; skipping migration", destination)
            return
        shutil.move(str(source), str(destination))

    def _ensure_repo_present(self) -> None:
        if self.config.repo_dir.exists() and (self.config.repo_dir / ".git").exists():
            return
        self.logger.info("Cloning repository from %s", self.config.repo_url)
        self.config.repo_dir.parent.mkdir(parents=True, exist_ok=True)
        self._run_command(
            [
                "git",
                "clone",
                self.config.repo_url,
                str(self.config.repo_dir),
            ],
            cwd=self.config.repo_dir.parent,
        )

    def acquire_wake_lock(self) -> None:
        """Acquire wake lock if supported (noop by default)."""

    def release_wake_lock(self) -> None:
        """Release wake lock if supported (noop by default)."""

    def ensure_safe_directory(self) -> None:
        if not self.config.auto_safe_directory:
            return
        repo_path = str(self.config.repo_dir)
        self.logger.debug("Registering git safe.directory for %s", repo_path)
        self._run_command(
            [
                "git",
                "config",
                "--global",
                "--add",
                "safe.directory",
                repo_path,
            ],
            check=False,
        )

    def sync_with_remote(self) -> None:
        """Synchronise repository with remote origin."""
        repo = self.config.repo_dir
        self.logger.info("Synchronising repository in %s", repo)
        self._ensure_repo_present()
        env = os.environ.copy()
        env.update(self.config.extra_env)
        self._run_command([
            "git",
            "fetch",
            self.config.git_remote,
            self.config.git_branch,
        ], cwd=repo, env=env)
        self._run_command([
            "git",
            "stash",
            "push",
            "-u",
            "-m",
            "evoruntime-auto",
        ], cwd=repo, env=env, check=False)
        self._run_command([
            "git",
            "reset",
            "--hard",
            f"{self.config.git_remote}/{self.config.git_branch}",
        ], cwd=repo, env=env)
        pop_result = self._run_command([
            "git",
            "stash",
            "pop",
        ], cwd=repo, env=env, check=False)
        if pop_result.returncode != 0:
            self.logger.warning("No stash to reapply or conflicts encountered")
        if self.config.push_changes:
            status = self._run_command([
                "git",
                "status",
                "--porcelain",
            ], cwd=repo, env=env)
            if status.stdout.strip():
                self._run_command([
                    "git",
                    "add",
                    "-A",
                ], cwd=repo, env=env)
                self._run_command([
                    "git",
                    "commit",
                    "-m",
                    "EvoRuntime auto-sync",
                ], cwd=repo, env=env, check=False)
                self._run_command([
                    "git",
                    "push",
                    self.config.git_remote,
                    f"HEAD:{self.config.git_branch}",
                    "--force-with-lease",
                ], cwd=repo, env=env, check=False)

    def build_entry_command(self) -> Sequence[str]:
        if not self.config.entry_point:
            return []
        return ["-m", self.config.entry_point, *self.config.entry_args]

    def execute_module(self, args: Sequence[str]) -> subprocess.Popen:
        python = str(self.config.python_bin or Path("python3"))
        command = [python, *args]
        self.logger.debug("Executing runtime module with command: %s", " ".join(command))
        return subprocess.Popen(command, cwd=self.config.repo_dir, start_new_session=True)

    def run(self) -> None:
        try:
            self.prepare()
            self.acquire_wake_lock()
            self.ensure_safe_directory()
            self.sync_with_remote()
            entry_command = self.build_entry_command()
            if entry_command:
                process = self.execute_module(entry_command)
                self.logger.info(
                    "Launched %s with PID %s",
                    self.config.entry_point,
                    process.pid,
                )
        finally:
            self.release_wake_lock()

    def _run_command(
        self,
        command: Sequence[str],
        cwd: Optional[Path] = None,
        env: Optional[Mapping[str, str]] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        self.logger.debug("Executing command: %s", " ".join(map(str, command)))
        result = subprocess.run(
            list(command),
            cwd=cwd or self.config.repo_dir,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            self.logger.debug(result.stdout.strip())
        if result.stderr:
            self.logger.debug(result.stderr.strip())
        if check and result.returncode != 0:
            raise RuntimeAdapterError(
                f"Command {' '.join(map(str, command))} failed with code {result.returncode}"
            )
        return result


__all__ = ["RuntimeAdapter", "RuntimeAdapterError"]
