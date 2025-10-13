"""Environment detection utilities for EvoLocalContext."""
from __future__ import annotations

import datetime
import json
import os
import platform
import socket
from pathlib import Path
from typing import Any, Dict

_REPORT_DIR = Path("apps/core/context/reports")


def _ensure_report_dir() -> Path:
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return _REPORT_DIR


def detect_environment() -> Dict[str, Any]:
    """Detect the runtime environment and persist a context snapshot."""
    env_type = "unknown"
    cwd = Path.cwd()

    if os.environ.get("ANDROID_ROOT") and Path("/data/data/com.termux").exists():
        env_type = "termux"
    elif "microsoft" in platform.uname().release.lower():
        env_type = "windows_wsl"
    elif "cloudshell" in str(cwd).lower():
        env_type = "cloud"
    elif platform.system().lower() in {"linux", "darwin", "windows"}:
        env_type = "desktop"

    payload: Dict[str, Any] = {
        "env_type": env_type,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cwd": str(cwd),
        "timestamp": datetime.datetime.now().isoformat(),
    }

    report_dir = _ensure_report_dir()
    report_path = report_dir / f"{env_type}_context.json"
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)

    return payload


__all__ = ["detect_environment"]
