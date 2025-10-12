import asyncio
import contextlib

from apps.core.time.evo_chrona import chrona, TemporalState


def test_chrona_pulse_smoke():
    async def runner():
        hits = {"n": 0}

        async def handler(_pulse):
            hits["n"] += 1

        original_tempo = chrona.tempo
        chrona.adjust_tempo(0.1)
        chrona.register_pulse_handler(handler)
        task = asyncio.create_task(chrona.pulse())
        await asyncio.sleep(0.3)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        chrona.unregister_pulse_handler(handler)
        chrona.adjust_tempo(original_tempo)
        assert hits["n"] >= 1

    asyncio.run(runner())


def test_chrona_state_adjust():
    chrona.adjust_tempo(1.5)
    assert 0.1 <= chrona.tempo <= 3.0
    chrona.change_temporal_state(TemporalState.REFLECTIVE)
    assert chrona.temporal_state == TemporalState.REFLECTIVE

import pytest

from apps.core.time import EvoChrona


@pytest.mark.asyncio
async def test_tempo_adjusts_pulse_rate() -> None:
    chrona = EvoChrona(base_interval=0.12, tempo=1.0)
    await chrona.start()

    async def measure(window: float, tempo: float) -> int:
        chrona.tempo = tempo
        before = chrona.pulse_count
        await asyncio.sleep(window)
        return chrona.pulse_count - before

    try:
        window = 0.6
        slow = await measure(window, 0.5)
        normal = await measure(window, 1.0)
        fast = await measure(window, 3.0)
    finally:
        await chrona.stop()

    assert slow < normal < fast
"""Tests for the EvoChrona Kairos moment persistence layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

import pytest

from apps.core.time.evo_chrona import EvoChrona, sanitize_moment_key


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


@pytest.mark.parametrize("forbidden_character", '<>:"/\\|?*')
def test_sanitize_moment_key_replaces_forbidden_characters(
    forbidden_character: str,
) -> None:
    sanitized = sanitize_moment_key(f"prefix{forbidden_character}suffix")

    assert forbidden_character not in sanitized
    assert sanitized == "prefix_suffix"


def test_sanitize_moment_key_replaces_whitespace() -> None:
    sanitized = sanitize_moment_key("Kairos moment")

    assert " " not in sanitized
    assert sanitized == "Kairos_moment"
