"""Smoke tests covering the EWA watcher lifecycle."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path

import pytest

from apps.core.memory import ewa_watcher
from apps.core.memory.ewa_watcher import Chrona, EWAWatcher
from apps.core.time.evo_chrona import chrona


def test_ewa_lifecycle(tmp_path, monkeypatch):
    async def runner() -> None:
        monkeypatch.chdir(tmp_path)
        initial_handlers = len(chrona._pulse_handlers)

        def fast_parse(self, _duration: str) -> timedelta:
            return timedelta(seconds=1)

        monkeypatch.setattr(
            ewa_watcher.EWAWatcher, "_parse_duration", fast_parse, raising=False
        )

        watcher = await ewa_watcher.create_ewa_watcher("sess_demo", "DemoProject", "1m")
        watcher.monitor_interval = 0.05
        watcher.capture_event("note", {"msg": "hello"})

        await asyncio.sleep(0.2)
        await asyncio.sleep(1.1)

        assert watcher._tasks == []
        assert len(chrona._pulse_handlers) == initial_handlers

        session_dir = Path("EvoMemory") / "ChronoSessions"
        assert (session_dir / "sess_demo_final.yaml").exists()

    asyncio.run(runner())


@pytest.mark.asyncio
async def test_ewa_watcher_records_and_cleans_up_handlers() -> None:
    """Ensure the watcher archives payloads and cleans up chrono handlers."""

    chrona_instance = Chrona()
    base_handler_count = chrona_instance.handler_count

    watcher = EWAWatcher("session-42", chrona_instance=chrona_instance)

    assert chrona_instance.handler_count == base_handler_count + 1

    await watcher.start()
    watcher.record({"message": "hello"})

    chrona_instance.emit_pulse()
    archive = watcher.archive
    assert len(archive) == 1
    assert archive[0].pulses[0].payload == {"message": "hello"}

    await watcher.teardown()

    assert chrona_instance.handler_count == base_handler_count
    assert watcher.background_task_count == 0
