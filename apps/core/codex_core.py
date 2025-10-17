"""Core utilities powering the EvoPyramid Codex API."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from apps.core.flow.context_engine import QuantumContext

LOGGER = logging.getLogger("evo.codex.core")

BASE_DIR = Path(__file__).resolve().parents[2]
CHRONICLE_PATH = BASE_DIR / "logs" / "codex_chronicles.jsonl"
SYNC_MANIFEST = BASE_DIR / "EVO_SYNC_MANIFEST.yaml"


def _ensure_logs_directory() -> None:
    CHRONICLE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _append_chronicle(entry: Dict[str, Any]) -> None:
    _ensure_logs_directory()
    enriched = {"timestamp": datetime.utcnow().isoformat() + "Z", **entry}
    with CHRONICLE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")


def _load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover - manifest parsing errors
        LOGGER.exception("Failed to read sync manifest: %s", exc)
        return {}


def get_sync_status() -> Dict[str, Any]:
    """Return sync manifest highlights for API exposure."""

    manifest = _load_manifest(SYNC_MANIFEST)
    policy = manifest.get("sync_policy", {})
    result = {
        "status": policy.get("mode", "unknown"),
        "authority": policy.get("authority"),
        "direction": policy.get("direction"),
        "codex_guard": policy.get("codex_guard", False),
        "last_revision": manifest.get("manifest", {}).get("last_revision"),
    }
    return result


def get_system_health() -> Dict[str, Any]:
    """Return lightweight health metrics used by the API."""

    chronicle_exists = CHRONICLE_PATH.exists()
    return {
        "chronicle_log": "available" if chronicle_exists else "missing",
        "entries_recorded": _count_chronicle_entries(CHRONICLE_PATH) if chronicle_exists else 0,
        "sync_manifest": "available" if SYNC_MANIFEST.exists() else "missing",
    }


def _count_chronicle_entries(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except FileNotFoundError:
        return 0
    except OSError as exc:  # pragma: no cover - IO guard
        LOGGER.warning("Unable to count chronicle entries: %s", exc)
        return 0


async def _process_with_context_engine(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    result = await QuantumContext.process(message, context)
    return {
        "summary": result.response,
        "coherence": result.coherence,
        "trace_id": result.trace_id,
        "design": result.design,
        "agents": result.agents_activated,
        "processing_time": result.processing_time,
    }


class CodexProcessor:
    """High-level orchestrator that bridges Codex queries to the context engine."""

    def __init__(self) -> None:
        self.logger = LOGGER.getChild("processor")

    async def process_query(self, message: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Process a message via the EvoPyramid context engine."""

        context = context or {}
        chronicle_entry: Dict[str, Any]
        try:
            payload = await _process_with_context_engine(message, context)
            payload["input"] = {"message": message, "context": context}
            chronicle_entry = {
                "type": "query",
                "message": message,
                "trace_id": payload["trace_id"],
                "coherence": payload["coherence"],
                "agents": payload["agents"],
            }
            return payload
        except Exception as exc:
            self.logger.exception("Codex query failed: %s", exc)
            chronicle_entry = {
                "type": "query_error",
                "message": message,
                "error": str(exc),
            }
            raise RuntimeError("Codex processing failed") from exc
        finally:
            try:
                _append_chronicle(chronicle_entry)
            except Exception as log_exc:  # pragma: no cover - logging safeguard
                self.logger.warning("Unable to append codex chronicle: %s", log_exc)


def propose_action(
    *,
    action_name: str,
    description: str,
    risk: Iterable[str] | None = None,
    alternatives: Iterable[str] | None = None,
) -> Dict[str, Any]:
    """Persist a proposed action and return its metadata."""

    entry = {
        "type": "action_proposal",
        "action_id": uuid.uuid4().hex,
        "action_name": action_name,
        "description": description,
        "risk": list(risk or []),
        "alternatives": list(alternatives or []),
    }
    _append_chronicle(entry)
    return entry


def get_recent_entries(*, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent chronicle entries in reverse chronological order."""

    if limit <= 0:
        return []
    if not CHRONICLE_PATH.exists():
        return []
    try:
        with CHRONICLE_PATH.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as exc:  # pragma: no cover - IO guard
        LOGGER.warning("Unable to read chronicle entries: %s", exc)
        return []

    records: List[Dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:  # pragma: no cover - skip malformed entries
            continue
    return records


__all__ = [
    "CodexProcessor",
    "get_sync_status",
    "get_system_health",
    "propose_action",
    "get_recent_entries",
]
