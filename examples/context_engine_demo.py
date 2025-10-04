"""Demonstration of the Quantum Context Engine integration."""

from __future__ import annotations

import asyncio

from apps.core.integration.context_engine import (
    enhanced_respond,
    get_context_engine,
    quick_analyze,
)


async def demo_evo_codex_integration() -> None:
    """Showcase how responses are generated through the integration layer."""

    queries = [
        "Как работает Quantum Context Analyzer?",
        "Нужна помощь с архитектурой EvoPyramid",
    ]
    for query in queries:
        response = await enhanced_respond(query)
        print("\n=== Ответ ===")
        print(response)


async def demo_memory_management() -> None:
    """Demonstrate adding data to the pyramid memory."""

    engine = get_context_engine()
    await engine.add_to_memory(
        {
            "name": "Новый контекст",
            "content": "Информация для демонстрации добавления фрагмента",
            "type": "functional",
            "weight": 0.75,
            "emotional_tone": "curiosity",
        }
    )
    analysis = await quick_analyze("Контекст демонстрации")
    print("\n=== Быстрый анализ ===")
    print(analysis)


async def main() -> None:
    await demo_evo_codex_integration()
    await demo_memory_management()


if __name__ == "__main__":
    print("Запуск демонстрации Quantum Context Engine...")
    asyncio.run(main())
