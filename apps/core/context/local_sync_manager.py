"""Local sync helpers for EvoLocalContext."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

_REPORT_DIR = Path("apps/core/context/reports")


def mark_local_request(source: str, query: str, result: str, env_type: str) -> None:
    """Append a structured log entry for local requests."""
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, str] = {
        "source": source,
        "query": query,
        "result_summary": (result or "")[:200],
        "env": env_type,
    }
    log_path = _REPORT_DIR / f"{env_type}_requests.log"
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


__all__ = ["mark_local_request"]
