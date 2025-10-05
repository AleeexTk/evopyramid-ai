"""Smoke tests covering the EWA watcher lifecycle."""

from __future__ import annotations

import pytest

from apps.core.memory.ewa_watcher import Chrona, EWAWatcher


@pytest.mark.asyncio
async def test_ewa_watcher_records_and_cleans_up_handlers() -> None:
    """Ensure the watcher archives payloads and cleans up chrono handlers."""

    chrona = Chrona()
    base_handler_count = chrona.handler_count

    watcher = EWAWatcher("session-42", chrona_instance=chrona)

    assert chrona.handler_count == base_handler_count + 1

    await watcher.start()
    watcher.record({"message": "hello"})

    chrona.emit_pulse()
    archive = watcher.archive
    assert len(archive) == 1
    assert archive[0].pulses[0].payload == {"message": "hello"}

    await watcher.teardown()

    assert chrona.handler_count == base_handler_count
    assert watcher.background_task_count == 0
