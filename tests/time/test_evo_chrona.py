"""Tests for the EvoChrona Kairos moment persistence layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

import pytest

from apps.core.time.evo_chrona import EvoChrona


class DummyMemory:
    """Simple in-memory storage to observe save operations."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def save_state(self, key: str, payload: Mapping[str, Any]) -> None:
        self.calls.append((key, payload))


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime(2024, 3, 20, 12, 34, 56, tzinfo=UTC),
        datetime(2024, 3, 20, 12, 34, 56),
    ],
)
def test_kairos_moment_filename_is_windows_safe(timestamp: datetime) -> None:
    chrona = EvoChrona(memory=DummyMemory())
    safe_key = chrona._save_kairos_moment(timestamp, {"event": "test"})

    forbidden_characters = '<>:"/\\|?*'
    assert all(char not in safe_key for char in forbidden_characters)
