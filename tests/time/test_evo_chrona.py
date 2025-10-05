import asyncio

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
