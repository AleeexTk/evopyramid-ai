from pathlib import Path
import sys
import types

import pytest

CORE_PACKAGE = "projects.evo_finart.core"
if CORE_PACKAGE not in sys.modules:
    core_stub = types.ModuleType(CORE_PACKAGE)
    core_stub.__path__ = [
        str(Path(__file__).resolve().parents[3] / "projects" / "evo_finart" / "core")
    ]
    sys.modules[CORE_PACKAGE] = core_stub

from projects.evo_finart.core.evo_insight_engine import (
    EvoInsightEngine,
    GeminiConfig,
    GeminiFinArtBridge,
    InsightPacket,
)


def test_engine_returns_disabled_status_when_gemini_disabled(tmp_path):
    config_path = tmp_path / "gemini_config.yaml"
    config_path.write_text("gemini:\n  enabled: false\n", encoding="utf-8")

    engine = EvoInsightEngine(config_path=config_path)

    packet = InsightPacket(topic="xauusd", payload={"bias": "long"})
    result = engine.process(packet)

    assert result["status"] == "gemini_disabled"
    assert result["gemini"] is None
    assert result["insight"]["topic"] == "xauusd"


def test_bridge_returns_placeholder_when_disabled():
    bridge = GeminiFinArtBridge(GeminiConfig(enabled=False))
    payload = {"topic": "test", "payload": {"message": "noop"}}

    reflection = bridge.reflect(payload)

    assert reflection.text == ""
    assert reflection.raw["status"] == "disabled"
    assert reflection.raw["insight"] == payload


def test_process_rejects_non_mapping_payload():
    engine = EvoInsightEngine(bridge=GeminiFinArtBridge(GeminiConfig(enabled=False)))

    with pytest.raises(TypeError):
        engine.process({"topic": "gold", "payload": "not-a-dict"})
