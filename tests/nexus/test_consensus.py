import asyncio
import importlib.util

import pytest

from apps.bridge.evonexus.nexus import EvoNexusBridge


async def _exercise_consensus(tmp_path, monkeypatch):
async def _async_test_nexus_basic_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("EVODIR", str(tmp_path / "EVO"))
    bridge = EvoNexusBridge()
    output = await bridge.run("Проверка Nexus/Consensus", session_id="TEST", seed=42)

    assert "verdict" in output
    assert output["verdict"]["decision"] in {"approve", "modify", "reject", "evolve"}
    assert (tmp_path / "EVO" / "nexus_logs").exists()


if importlib.util.find_spec("pytest_asyncio") is not None:

    @pytest.mark.asyncio
    async def test_nexus_basic_flow(tmp_path, monkeypatch):
        await _exercise_consensus(tmp_path, monkeypatch)

else:

    def test_nexus_basic_flow(tmp_path, monkeypatch):
        asyncio.run(_exercise_consensus(tmp_path, monkeypatch))
def test_nexus_basic_flow(tmp_path, monkeypatch):
    asyncio.run(_async_test_nexus_basic_flow(tmp_path, monkeypatch))
