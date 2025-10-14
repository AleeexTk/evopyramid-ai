import asyncio
from typing import Awaitable


async def initialize_temporal_architecture() -> Awaitable[None]:
    from apps.core.time.evo_chrona import chrona
    from apps.core.monitoring.flow_monitor import FlowMonitor

    chrona_task = asyncio.create_task(chrona.pulse())
    FlowMonitor.register_tempo_handler(chrona.adjust_tempo)
    FlowMonitor.register_state_handler(chrona.change_temporal_state)
    print("🌀 EvoChrona activated")
    return chrona_task
