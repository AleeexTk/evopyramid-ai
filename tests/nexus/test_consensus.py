import pytest

from apps.bridge.evonexus.nexus import EvoNexusBridge


@pytest.mark.asyncio
async def test_nexus_basic_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("EVODIR", str(tmp_path / "EVO"))
    bridge = EvoNexusBridge()
    output = await bridge.run("Проверка Nexus/Consensus", session_id="TEST", seed=42)

    assert "verdict" in output
    assert output["verdict"]["decision"] in {"approve", "modify", "reject", "evolve"}
    assert (tmp_path / "EVO" / "nexus_logs").exists()
