"""Integration checks for the EvoAbsolute laboratory adapter."""

from __future__ import annotations

import json
from pathlib import Path

from roles.evo_absolute.lab.visual_env_adapter import VisualEnvAdapter


def test_visual_env_adapter_creates_logs(tmp_path: Path) -> None:
    adapter = VisualEnvAdapter(log_root=tmp_path)

    summary = adapter.summarize_lab()
    assert "manifest" in summary
    assert (tmp_path / "finart_bridge.log").exists()

    event = adapter.emit_link_event(status="test", details={"origin": "pytest"})
    assert event["status"] == "test"

    sync_log = tmp_path / "sync.log"
    assert sync_log.exists()
    logged = sync_log.read_text(encoding="utf-8").strip().splitlines()
    assert logged, "sync log should contain at least one event"
    payload = json.loads(logged[-1])
    assert payload["details"]["origin"] == "pytest"

    reflection = tmp_path / "reflection.json"
    assert json.loads(reflection.read_text(encoding="utf-8"))["status"] == "test"
