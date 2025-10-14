"""Integration tests for EvoMetaCore context engine wiring."""

import pytest

pytest.importorskip("requests", reason="requests dependency required for EvoMetaCore tests")

from apps.core.evo_core import EvoMetaCore


def test_process_context_query_returns_response() -> None:
    """Quantum Context Engine should return a structured response."""

    core = EvoMetaCore()
    result = core.process_context_query("Привет, расскажи о своей памяти")
    assert isinstance(result, dict)
    assert "response" in result
    assert "success" in result


def test_process_task_routes_to_context_engine() -> None:
    """process_task should route context queries when requested."""

    core = EvoMetaCore()
    result = core.process_task(
        {
            "type": "context_query",
            "data": "Какая текущая срочность?",
            "use_context_engine": True,
        }
    )
    assert "context_engine" in result
    assert result["context_engine"].get("response")
