import asyncio
import contextlib
from datetime import timedelta
from pathlib import Path

from apps.core.memory import ewa_watcher
from apps.core.time.evo_chrona import chrona


def test_ewa_lifecycle(tmp_path, monkeypatch):
    async def runner():
        monkeypatch.chdir(tmp_path)

        def fast_parse(self, _duration: str) -> timedelta:
            return timedelta(seconds=1)

        monkeypatch.setattr(
            ewa_watcher.EWAWatcher, "_parse_duration", fast_parse, raising=False
        )

        watcher = await ewa_watcher.create_ewa_watcher("sess_demo", "DemoProject", "1m")
        watcher.monitor_interval = 0.05
        watcher.capture_event("note", {"msg": "hello"})

        await asyncio.sleep(0.2)
        await asyncio.sleep(1.2)

        chrona.unregister_pulse_handler(watcher._on_chrono_pulse)
        for task in watcher._tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        session_dir = Path("EvoMemory") / "ChronoSessions"
        assert any(session_dir.glob("sess_demo_final.yaml"))

    asyncio.run(runner())
