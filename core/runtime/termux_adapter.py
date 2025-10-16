"""Termux runtime adapter implementation."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Sequence

from .config import RuntimeConfig
from .environment import RuntimeAdapter


class TermuxAdapter(RuntimeAdapter):
    """Adapter that integrates EvoPyramid with a Termux node."""

    def __init__(self, config: RuntimeConfig, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(config, logger)
        self._wake_lock_acquired = False

    def acquire_wake_lock(self) -> None:
        wake_bin = shutil.which("termux-wake-lock")
        if not wake_bin:
            self.logger.debug("termux-wake-lock binary not available")
            return
        result = self._run_command([wake_bin], check=False)
        if result.returncode == 0:
            self._wake_lock_acquired = True
            self.logger.info("Wake lock acquired")
        else:
            self.logger.warning("Unable to acquire wake lock: %s", result.stderr.strip())

    def release_wake_lock(self) -> None:
        if not self._wake_lock_acquired:
            return
        unlock_bin = shutil.which("termux-wake-unlock")
        if not unlock_bin:
            self.logger.debug("termux-wake-unlock binary not available")
            return
        result = self._run_command([unlock_bin], check=False)
        if result.returncode == 0:
            self.logger.info("Wake lock released")
            self._wake_lock_acquired = False
        else:
            self.logger.warning("Wake lock release returned non-zero: %s", result.stderr.strip())

    def _prepare_directories(self) -> None:
        super()._prepare_directories()
        self.config.repo_dir.parent.mkdir(parents=True, exist_ok=True)

    def _relocate_repository(self, source: Path, destination: Path) -> None:
        self.logger.debug("Relocating repository from %s to %s", source, destination)
        try:
            super()._relocate_repository(source, destination)
        except PermissionError as exc:  # pragma: no cover - depends on device FS
            self.logger.warning("Permission error during migration: %s", exc)

    def execute_module(self, args: Sequence[str]) -> subprocess.Popen:
        python = str(self.config.python_bin or Path("/data/data/com.termux/files/usr/bin/python3"))
        env: Dict[str, str] = dict(os.environ)
        env.update(self.config.extra_env)
        command = [python, *args]
        self.logger.debug("Launching module via Termux adapter: %s", " ".join(command))
        return subprocess.Popen(command, cwd=self.config.repo_dir, env=env, start_new_session=True)

