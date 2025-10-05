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
