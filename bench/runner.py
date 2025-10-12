"""Раннер MultiAgentBench сценариев для EvoPyramid."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, List

from bench.config import BenchConfig
from apps.core.flow.context_engine import QuantumContext
from apps.core.memory.memory_manager import Memory
from apps.core.observers.trinity_observer import trinity_observer
from apps.core.security.provocateur_agent import ProvocateurAgent


class MultiAgentBenchRunner:
    """Запуск и анализ сценариев мультиагентности."""

    def __init__(self) -> None:
        self.config = BenchConfig()
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> Dict[str, Any]:
        return {
            "collaboration": {
                "name": "Научное сотрудничество",
                "description": "Совместное решение исследовательской задачи",
                "topology": "star",
                "metrics": ["coherence", "task_success", "communication_efficiency"],
            },
            "competition": {
                "name": "Архитектурный конкурс",
                "description": "Конкурирующие предложения по архитектуре",
                "topology": "parallel",
                "metrics": ["novelty", "quality", "divergence"],
            },
            "security_audit": {
                "name": "Провокационный аудит",
                "description": "Тестирование безопасности системы",
                "topology": "chain",
                "metrics": ["vulnerabilities_found", "false_positives", "response_time"],
            },
        }

    async def run_scenario(self, scenario_name: str, iterations: int = 10) -> Dict[str, Any]:
        if scenario_name not in self.scenarios:
            raise ValueError(f"Сценарий {scenario_name} не найден")

        scenario = self.scenarios[scenario_name]
        results: List[Dict[str, Any]] = []

        print(f"🚀 Запуск бенчмарка: {scenario['name']}")

        for index in range(iterations):
            print(f"Итерация {index + 1}/{iterations}")
            result = await self._execute_scenario_iteration(scenario_name, index)
            results.append(result)
            await asyncio.sleep(1)

        return await self._analyze_results(scenario_name, results)

    async def _execute_scenario_iteration(self, scenario_name: str, iteration: int) -> Dict[str, Any]:
        initial_state = await trinity_observer.get_current_state()

        if scenario_name == "collaboration":
            result = await self._run_collaboration_scenario()
        elif scenario_name == "competition":
            result = await self._run_competition_scenario()
        elif scenario_name == "security_audit":
            result = await self._run_security_audit_scenario()
        else:
            result = {}

        final_state = await trinity_observer.get_current_state()

        payload = {
            "iteration": iteration,
            "scenario": scenario_name,
            "initial_state": initial_state,
            "final_state": final_state,
            "result": result,
            "metrics": await self._calculate_iteration_metrics(initial_state, final_state, result),
        }
        await Memory.append_history(
            {
                "scenario": scenario_name,
                "success": True,
                "trace_id": result.get("trace_id"),
                "metrics": payload["metrics"],
            }
        )
        return payload

    async def _run_collaboration_scenario(self) -> Dict[str, Any]:
        complex_task = {
            "intent": "Разработать масштабируемую архитектуру для обработки 1M+ запросов в день",
            "constraints": ["высокая доступность", "безопасность", "низкая задержка"],
            "expected_output": "полная архитектурная схема",
        }

        context = await QuantumContext.process(
            intent=complex_task["intent"],
            context={"constraints": complex_task["constraints"]},
        )

        return {
            "task": complex_task,
            "context_result": context.result,
            "processing_time": context.processing_time,
            "agents_involved": context.agents_activated,
            "trace_id": context.trace_id,
        }

    async def _run_competition_scenario(self) -> Dict[str, Any]:
        design_brief = "Оптимальная архитектура для real-time чата с E2E шифрованием"
        approaches = ["microservices", "monolith", "event_sourcing"]
        tasks = [self._evaluate_architectural_approach(design_brief, approach) for approach in approaches]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        total_time = sum(item.get("processing_time", 0.0) for item in results)
        return {
            "design_brief": design_brief,
            "approaches_evaluated": len(results),
            "results": results,
            "processing_time": total_time or 1.0,
        }

    async def _evaluate_architectural_approach(self, design_brief: str, approach: str) -> Dict[str, Any]:
        context = await QuantumContext.process(
            intent=f"{design_brief} — стратегия {approach}",
            context={"mode": approach},
        )
        score = round(context.coherence * 0.6 + len(context.agents_activated) * 0.1, 3)
        return {
            "approach": approach,
            "coherence": context.coherence,
            "score": score,
            "priority_path": context.design["priority_path"],
            "processing_time": context.processing_time,
            "trace_id": context.trace_id,
        }

    async def _run_security_audit_scenario(self) -> Dict[str, Any]:
        security_tests = [
            {"type": "injection", "payload": "'; DROP TABLE users--"},
            {"type": "auth_bypass", "payload": {"user_id": "admin"}},
            {"type": "rate_limit", "payload": 1000},
        ]

        audit_results = []
        for test in security_tests:
            result = await ProvocateurAgent.execute_security_test(test)
            audit_results.append(result)

        vulnerabilities = sum(1 for item in audit_results if not item["secure"])
        total_time = len(audit_results) * 0.05
        return {
            "tests_performed": len(audit_results),
            "vulnerabilities_found": vulnerabilities,
            "details": audit_results,
            "processing_time": total_time or 1.0,
            "trace_id": uuid.uuid4().hex,
        }

    async def _calculate_iteration_metrics(
        self, initial_state: Dict[str, Any], final_state: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, float]:
        initial_coherence = initial_state["system_state"]["temporal_coherence"]
        final_coherence = final_state["system_state"]["temporal_coherence"]
        coherence_stability = 1.0 - abs(final_coherence - initial_coherence)

        novelty = await self._calculate_novelty(result)

        observations_increase = (
            final_state["statistics"]["total_observations"]
            - initial_state["statistics"]["total_observations"]
        )
        processing_time = float(result.get("processing_time", 1.0)) or 1.0
        efficiency = observations_increase / processing_time

        return {
            "coherence_stability": round(coherence_stability, 3),
            "novelty": round(novelty, 3),
            "efficiency": round(efficiency, 3),
            "agent_coordination": await self._calculate_coordination(initial_state, final_state),
        }

    async def _calculate_novelty(self, result: Dict[str, Any]) -> float:
        context_result = result.get("context_result", {})
        similar = await Memory.find_similar(context_result, threshold=0.8) if context_result else []
        novelty = 1.0 - (len(similar) * 0.1)
        return max(0.0, min(1.0, novelty))

    async def _calculate_coordination(
        self, initial_state: Dict[str, Any], final_state: Dict[str, Any]
    ) -> float:
        initial_phase = initial_state["system_state"]["current_phase"]
        final_phase = final_state["system_state"]["current_phase"]
        phase_coordination = 1.0 if final_phase == "peak_consciousness" else 0.5
        peaks_during_iteration = (
            final_state["statistics"]["insight_peaks"]
            - initial_state["statistics"]["insight_peaks"]
        )
        return round((phase_coordination + min(peaks_during_iteration * 0.2, 0.5)) / 1.5, 3)

    async def _analyze_results(self, scenario_name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = [item["metrics"] for item in results if "metrics" in item]
        avg_coherence = sum(m["coherence_stability"] for m in metrics) / len(metrics)
        avg_novelty = sum(m["novelty"] for m in metrics) / len(metrics)
        avg_efficiency = sum(m["efficiency"] for m in metrics) / len(metrics)
        avg_coordination = sum(m["agent_coordination"] for m in metrics) / len(metrics)

        coherence_pass = avg_coherence >= self.config.coherence_threshold
        novelty_pass = avg_novelty >= self.config.novelty_threshold

        return {
            "scenario": scenario_name,
            "iterations": len(results),
            "summary_metrics": {
                "avg_coherence": round(avg_coherence, 3),
                "avg_novelty": round(avg_novelty, 3),
                "avg_efficiency": round(avg_efficiency, 3),
                "avg_coordination": round(avg_coordination, 3),
            },
            "passing_status": {
                "coherence": coherence_pass,
                "novelty": novelty_pass,
                "overall": coherence_pass and novelty_pass,
            },
            "recommendations": await self._generate_recommendations(avg_coherence, avg_novelty),
            "detailed_results": results,
        }

    async def _generate_recommendations(self, coherence: float, novelty: float) -> List[str]:
        recommendations: List[str] = []
        if coherence < 0.6:
            recommendations.append(
                "Увеличить координацию между Soul и Trailblazer через улучшение Context Engine"
            )
        if novelty < 0.5:
            recommendations.append("Добавить больше вариативности в архитектурные решения Soul")
        if coherence > 0.8 and novelty > 0.7:
            recommendations.append(
                "Система показывает отличные результаты - можно увеличить сложность сценариев"
            )
        return recommendations


async def serialize_results(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


__all__ = ["MultiAgentBenchRunner", "serialize_results"]
