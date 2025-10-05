import asyncio
from datetime import timedelta
from pathlib import Path

from apps.core.memory import ewa_watcher
from apps.core.time.evo_chrona import chrona


def test_ewa_lifecycle(tmp_path, monkeypatch):
    async def runner():
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
