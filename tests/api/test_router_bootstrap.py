"""Tests for manifest-driven EvoRouter bootstrapping."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from api import (
    EvoRouter,
    ManifestError,
    bootstrap_router_from_manifest,
    load_manifest,
)
from api.schemas.base import KairosMoment


def test_bootstrap_registers_routes_from_canonical_manifest() -> None:
    router = EvoRouter()
    manifest = load_manifest()

    bootstrap_router_from_manifest(router, manifest=manifest)

    spec = router.get("memory_store")
    moment = KairosMoment(
        identifier="kairos-1",
        narrative="Stability calibration",
        resonance="Logos",
        importance=5,
        timestamp=datetime(2025, 1, 1, 0, 0, 0),
    )

    acknowledgement = spec.handler(moment)
    assert acknowledgement["status"] == "accepted"
    assert acknowledgement["moment_id"] == moment.identifier


def test_bootstrap_raises_for_invalid_handler(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    yaml.safe_dump(
        {
            "routes": [
                {
                    "id": "broken",
                    "path": "/broken",
                    "method": "POST",
                    "scope": "internal",
                    "handler": "api.endpoints.core.missing",
                    "description": "Broken handler reference",
                }
            ]
        },
        manifest_path.open("w", encoding="utf-8"),
        sort_keys=False,
    )

    router = EvoRouter()

    with pytest.raises(ManifestError) as error:
        bootstrap_router_from_manifest(router, manifest_path=manifest_path)

    assert "Handler attribute" in str(error.value)
