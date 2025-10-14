"""Integration tests for the context engine and memory linkage."""

import asyncio

from apps.core.integration.context_engine import EvoCodexContextEngine
from apps.core.memory.pyramid_memory import (
    EnhancedDigitalSoulLedger,
    PyramidMemory,
)


def test_context_engine_shares_memory_instance(tmp_path) -> None:
    memory_file = tmp_path / "engine_memory.xml"
    memory = PyramidMemory(str(memory_file))
    engine = EvoCodexContextEngine(memory_system=memory)

    fragment_id = "test_sync_fragment"
    fragment_content = "уникальный маркер контекста"

    async def _store_and_fetch() -> dict[str, object]:
        await engine.add_to_memory(
            {
                "id": fragment_id,
                "name": "Тестовый синхронизированный фрагмент",
                "content": fragment_content,
                "type": "core",
                "weight": 0.9,
            }
        )
        return await engine.enhanced_ledger.find_related_fragments(
            fragment_content,
            threshold=0.2,
        )

    results = asyncio.run(_store_and_fetch())

    assert fragment_id in results.fragments, "Новый фрагмент должен быть доступен через ledger"
    assert memory_file.exists(), "Файл памяти должен быть создан"


def test_context_engine_refreshes_ledger_after_add(tmp_path) -> None:
    memory_file = tmp_path / "engine_refresh_memory.xml"
    primary_memory = PyramidMemory(str(memory_file))
    engine = EvoCodexContextEngine(memory_system=primary_memory)

    # Simulate a ledger that references the same XML file but a different PyramidMemory instance.
    engine.enhanced_ledger = EnhancedDigitalSoulLedger(
        PyramidMemory(str(memory_file)),
        auto_reload=False,
    )

    fragment_id = "refresh_fragment"
    fragment_content = "освежающий маркер синхронизации"

    async def _store_and_fetch() -> dict[str, object]:
        await engine.add_to_memory(
            {
                "id": fragment_id,
                "name": "Фрагмент для проверки обновления ledger",
                "content": fragment_content,
                "type": "core",
                "weight": 0.8,
            }
        )
        return await engine.enhanced_ledger.find_related_fragments(
            fragment_content,
            threshold=0.2,
        )

    results = asyncio.run(_store_and_fetch())

    assert fragment_id in results.fragments, "Ledger должен видеть фрагмент после обновления"
