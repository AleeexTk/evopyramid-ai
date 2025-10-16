"""Async endpoint tests for the public API surface."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict

import pytest
import pytest_asyncio

httpx = pytest.importorskip("httpx")
from httpx import ASGITransport, AsyncClient  # type: ignore  # noqa: E402

from apps.api.main import app
from apps.core.memory.memory_manager import Memory


@pytest_asyncio.fixture
async def api_key() -> AsyncIterator[str]:
    """Register a deterministic API key inside the in-memory storage."""

    previous_keys = await Memory.get("api_keys")
    test_key = "test-suite-api-key"
    await Memory.set("api_keys", [test_key])
    try:
        yield test_key
    finally:
        if previous_keys is None:
            await Memory.set("api_keys", [])
        else:
            # Ensure we restore the original list instance.
            await Memory.set("api_keys", list(previous_keys))


@pytest_asyncio.fixture
def stub_trinity(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide a deterministic Trinity observer for metrics and health checks."""

    state = {
        "timestamp": "2024-01-01T00:00:00+00:00",
        "observer_mode": "guardian",
        "system_state": {"temporal_coherence": 0.87, "current_phase": "stability"},
        "statistics": {
            "total_observations": 42,
            "insight_peaks": 7,
            "active_agents": 3,
        },
    }

    async def get_current_state() -> Dict[str, Any]:
        return state

    recorded: list[tuple[str, str]] = []

    async def record_interaction(node: str, trace_id: str) -> None:
        recorded.append((node, trace_id))

    observer = SimpleNamespace(
        get_current_state=get_current_state,
        record_interaction=record_interaction,
        recorded=recorded,
        state=state,
    )

    monkeypatch.setattr("apps.api.endpoints.agents.trinity_observer", observer)
    monkeypatch.setattr("apps.api.endpoints.metrics.trinity_observer", observer)
    monkeypatch.setattr("apps.api.endpoints.health.trinity_observer", observer)

    return observer


@pytest_asyncio.fixture
def stub_quantum(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Mock the QuantumContext to avoid heavy upstream dependencies."""

    result = SimpleNamespace(
        design={
            "summary": "Deterministic architecture",
            "priority_path": "SOUL",
            "intent": {"goal": "stability"},
            "affect": {"soul_resonance": 0.8},
            "memory": {"relevance_score": 0.7},
            "processing_time": 0.12,
        },
        coherence=0.93,
        trace_id="trace-abc123",
    )

    async def process(intent: str, context: Dict[str, Any]) -> SimpleNamespace:
        return result

    monkeypatch.setattr("apps.api.endpoints.agents.QuantumContext.process", process)

    return result


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Provide an AsyncClient bound to the FastAPI app."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_soul_design_returns_agent_response_schema(
    async_client: AsyncClient,
    api_key: str,
    stub_quantum: SimpleNamespace,
    stub_trinity: SimpleNamespace,
) -> None:
    """POST /api/soul/design should return the AgentResponse schema."""

    del stub_trinity  # interaction tracking is covered by schema assertions

    payload = {"intent": "stabilize", "context": {"focus": "testing"}}
    response = await async_client.post(
        "/api/soul/design",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200

    data = response.json()
    assert data == {
        "response": stub_quantum.design,
        "coherence": stub_quantum.coherence,
        "trace_id": stub_quantum.trace_id,
    }


@pytest.mark.asyncio
async def test_health_endpoint_reflects_stubbed_state(
    async_client: AsyncClient, stub_trinity: SimpleNamespace
) -> None:
    """GET /api/health should return the deterministic observer snapshot."""

    response = await async_client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["timestamp"] == stub_trinity.state["timestamp"]
    assert data["system"]["active_agents"] == stub_trinity.state["statistics"]["active_agents"]


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_payload(
    async_client: AsyncClient, stub_trinity: SimpleNamespace
) -> None:
    """GET /api/metrics should expose Prometheus metrics when enabled."""

    response = await async_client.get("/api/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    body = response.text
    assert "evopyramid_requests_total" in body
    assert "evopyramid_active_agents" in body
    assert "3.0" in body  # active_agents gauge reflects the stubbed state
