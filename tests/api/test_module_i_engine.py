from __future__ import annotations

import pytest

from apps.core.module_i import ModuleIEngine


@pytest.mark.asyncio
async def test_module_i_engine_analyze_produces_structured_output() -> None:
    engine = ModuleIEngine()
    result = await engine.analyze(
        "Спроектируй архитектуру модульного API EvoPyramid",
        {"session_length": 12, "deep_analysis": True},
    )

    assert result["intent"]["kind"] in {"TECHNICAL", "META", "OTHER"}
    assert "collective_mind" in result
    assert result["collective_mind"]["mode"] in {
        "chaos_redirection",
        "fundamental_memory",
    }
    assert result["codex_analysis"]["summary"]
    assert result["role_panel"]["panel"]
    assert result["recommendations"]
    assert result["synergy"] is not None


@pytest.mark.asyncio
async def test_module_i_engine_status_reflects_last_analysis() -> None:
    engine = ModuleIEngine()
    await engine.analyze(
        "Оцени эмоциональную устойчивость архитектуры EvoPyramid",
        {"force_synergy": True},
    )

    status = engine.status()
    assert status["module"] == "Module I"
    assert status["last_intent"] is not None
    assert status["last_codex_snapshot"] is not None
    assert "coherence" in status["last_codex_snapshot"]
