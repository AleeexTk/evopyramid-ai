"""Device metric collection helpers for EvoLocalContext."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict

try:  # Optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil is optional
    psutil = None  # type: ignore

_REPORT_DIR = Path("apps/core/context/reports")


def _ensure_report_dir() -> Path:
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return _REPORT_DIR


def analyze_device() -> Dict[str, Any]:
    """Collect basic device metrics and persist them for Trinity."""
    payload: Dict[str, Any] = {"timestamp": datetime.datetime.now().isoformat()}

    if psutil is None:
        payload["note"] = "psutil not available; metrics skipped"
    else:
        try:
            payload.update(
                {
                    "cpu_percent": psutil.cpu_percent(interval=0.5),
                    "memory": getattr(psutil.virtual_memory(), "_asdict", lambda: {})(),
                    "disk": getattr(psutil.disk_usage("/"), "_asdict", lambda: {})(),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            payload["warning"] = f"psutil read failed: {exc}"

    report_dir = _ensure_report_dir()
    report_path = report_dir / "device_stats.json"
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)

    return payload


__all__ = ["analyze_device"]
