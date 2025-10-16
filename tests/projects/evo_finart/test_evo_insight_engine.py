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


def test_engine_redacts_api_key_from_public_config(tmp_path):
    config_path = tmp_path / "gemini_config.yaml"
    config_path.write_text(
        """gemini:
  enabled: false
  api_key: super-secret
  model: gemini-1.5-flash
""",
        encoding="utf-8",
    )

    engine = EvoInsightEngine(config_path=config_path)
    packet = InsightPacket(topic="xauusd", payload={"bias": "long"})
    result = engine.process(packet)

    gemini_config = result["config"]["gemini"]
    assert "api_key" not in gemini_config
    assert gemini_config["model"] == "gemini-1.5-flash"


def test_bridge_to_dict_optionally_includes_sensitive_values():
    config = GeminiConfig(api_key="top-secret-token", enabled=True)
    bridge = GeminiFinArtBridge(config)

    public_view = bridge.to_dict()
    assert "api_key" not in public_view

    internal_view = bridge.to_dict(include_sensitive=True)
    assert internal_view["api_key"] == "top-secret-token"
