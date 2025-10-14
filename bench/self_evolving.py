"""Self-evolving evaluations из COLING-2025."""

from __future__ import annotations

from typing import Any, Dict, List

from apps.core.memory.memory_manager import Memory


class SelfEvolvingEvals:
    def __init__(self) -> None:
        self.learning_datasets: List[Dict[str, Any]] = []

    async def generate_new_scenarios(self, base_scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        new_scenarios: List[Dict[str, Any]] = []
        for scenario in base_scenarios:
            successful_runs = await self._get_successful_runs(scenario["name"])
            for run in successful_runs:
                variant = await self._create_scenario_variant(scenario, run)
                new_scenarios.append(variant)
        return new_scenarios

    async def expand_skill_dataset(self, new_skills: List[Dict[str, Any]]) -> None:
        for skill in new_skills:
            await Memory.save_state(
                f"bench_skill_{skill['type']}",
                skill,
                category="self_evolving_skills",
            )
            self.learning_datasets.append(skill)

    async def _get_successful_runs(self, scenario_name: str) -> List[Dict[str, Any]]:
        history = await Memory.get("bench_history", [])
        return [entry for entry in history if entry.get("scenario") == scenario_name and entry.get("success")]

    async def _create_scenario_variant(
        self, scenario: Dict[str, Any], run: Dict[str, Any]
    ) -> Dict[str, Any]:
        variant = scenario.copy()
        variant["name"] = f"{scenario['name']} ++"
        variant["seed_trace"] = run.get("trace_id")
        variant["difficulty_multiplier"] = run.get("metrics", {}).get("coherence_stability", 0.7) + 0.1
        return variant


__all__ = ["SelfEvolvingEvals"]
