from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


def test_localhost_is_allowed_by_default() -> None:
    """Ensure localhost headers pass through TrustedHostMiddleware."""

    client = TestClient(app)
    response = client.get("/", headers={"host": "localhost"})
    assert response.status_code != 400
