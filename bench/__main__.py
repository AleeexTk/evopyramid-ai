"""CLI интерфейс для запуска бенчмарков."""

from __future__ import annotations

import asyncio
import json
import sys

from bench.runner import MultiAgentBenchRunner


async def main() -> None:
    runner = MultiAgentBenchRunner()

    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
        iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        result = await runner.run_scenario(scenario_name, iterations)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    scenarios = ["collaboration", "competition", "security_audit"]
    results = {}

    for scenario in scenarios:
        print(f"\n{'=' * 50}")
        print(f"Запуск сценария: {scenario}")
        print(f"{'=' * 50}")
        result = await runner.run_scenario(scenario, iterations=3)
        results[scenario] = result
        status = "✅ PASS" if result["passing_status"]["overall"] else "❌ FAIL"
        print(f"Результат: {status}")
        print(f"Coherence: {result['summary_metrics']['avg_coherence']}")
        print(f"Novelty: {result['summary_metrics']['avg_novelty']}")

    print(f"\n{'=' * 50}")
    print("СВОДНЫЙ ОТЧЁТ MULTIAGENT BENCH")
    print(f"{'=' * 50}")
    for scenario, result in results.items():
        status = "PASS" if result["passing_status"]["overall"] else "FAIL"
        print(
            f"{scenario:20} {status:6} "
            f"Coherence: {result['summary_metrics']['avg_coherence']:.3f} "
            f"Novelty: {result['summary_metrics']['avg_novelty']:.3f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
