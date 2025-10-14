"""Command line utility to experiment with the enhanced EvoNexus bridge."""
from __future__ import annotations

import argparse
import asyncio

from apps.bridge.evonexus.enhanced_fusion import EnhancedEvoNexusBridge


async def run_cli(args: argparse.Namespace) -> None:
    bridge = EnhancedEvoNexusBridge()
    result = await bridge.deep_process(args.proposal, args.session)

    print("\n=== 🧠 ENHANCED EVONEXUS BRIDGE ===")
    print(f"Предложение: {result['proposal']}")
    print(f"Сессия: {result['session_id']}")

    insight = result["deep_insight"]
    print("\n🎯 ГЛУБОКИЙ ИНСАЙТ:")
    print(f"   {insight['core_understanding']}")

    emotional = insight["emotional_context"]
    print("\n💫 ЭМОЦИОНАЛЬНЫЙ КОНТЕКСТ:")
    print(f"   {emotional['description']}")
    print(f"   Интенсивность: {emotional['intensity']:.2f}")
    print(f"   Резонанс: {emotional['resonance']:.2f}")

    print("\n🔗 РЕЗОНАНСЫ ПАМЯТИ:")
    for resonance in insight["memory_resonance"]:
        print(f"   • {resonance}")

    print("\n🎨 ТВОРЧЕСКОЕ НАПРАВЛЕНИЕ:")
    print(f"   {insight['creative_direction']}")

    print("\n📚 СИМВОЛИЧЕСКАЯ МЕТАФОРА:")
    print(f"   {insight['symbolic_metaphor']}")

    print(f"\n📊 СЛОЖНОСТЬ ИНСАЙТА: {insight['complexity_score']:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhanced EvoNexusBridge CLI")
    parser.add_argument("--proposal", required=True, help="Текст предложения для глубокого анализа")
    parser.add_argument("--session", default="PEAR_A24", help="ID сессии")

    args = parser.parse_args()
    asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
