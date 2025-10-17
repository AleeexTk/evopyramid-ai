"""High-level analytical engine powering Module I endpoints."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List, Optional

from apps.core.agi_proto.roles import RoleProposal, run_role_panel
from apps.core.flow.context_engine import QuantumContext
from apps.core.intent.collective_mind import (
    EvoCollectiveMind,
    EvoSynergyOrchestrator,
    MemoryMode,
)
from apps.core.intent.intent_classifier import IntentSignal, IntentStreamClassifier


class ModuleIEngine:
    """Coordinate intent analysis, memory orchestration and role feedback."""

    def __init__(self) -> None:
        self.intent_classifier = IntentStreamClassifier()
        self.collective_mind = EvoCollectiveMind()
        self.synergy_orchestrator = EvoSynergyOrchestrator()
        self._last_signal: Optional[IntentSignal] = None
        self._last_codex_snapshot: Dict[str, Any] | None = None

    async def analyze(self, question: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Run a full Module I analysis cycle for the provided question."""

        context = context or {}
        intent_signal = self.intent_classifier.classify(question)
        self._last_signal = intent_signal

        enriched_context = {
            **context,
            "intent_signal": intent_signal.kind,
            "intent_confidence": intent_signal.confidence,
            "intent_features": intent_signal.features,
        }

        mind_result, codex_result = await asyncio.gather(
            self.collective_mind.process_intent(question, enriched_context),
            QuantumContext.process(question, enriched_context),
        )

        synergy_result: Dict[str, Any] | None = None
        if self._should_trigger_synergy(intent_signal, context):
            synergy_result = await self.synergy_orchestrator.orchestrate_quad_processing(
                question,
                enriched_context,
            )

        role_proposals = run_role_panel(question, enriched_context)

        codex_payload = {
            "summary": codex_result.response,
            "coherence": codex_result.coherence,
            "trace_id": codex_result.trace_id,
            "priority_path": codex_result.design["priority_path"],
            "agents": codex_result.agents_activated,
            "processing_time": codex_result.processing_time,
            "design": codex_result.design,
        }
        self._last_codex_snapshot = codex_payload

        analysis = {
            "intent": self._intent_to_dict(intent_signal),
            "collective_mind": mind_result,
            "codex_analysis": codex_payload,
            "role_panel": self._serialize_roles(role_proposals),
            "synergy": synergy_result,
            "recommendations": self._build_recommendations(
                intent_signal,
                mind_result,
                codex_payload,
                synergy_result,
            ),
        }
        return analysis

    def status(self) -> Dict[str, Any]:
        """Expose current Module I operational status."""

        memory_mode: MemoryMode = self.collective_mind.memory_mode
        return {
            "status": "active",
            "module": "Module I",
            "memory_mode": memory_mode.value,
            "capabilities": [
                "intent_classification",
                "collective_memory_alignment",
                "codex_context_projection",
                "role_panel_consensus",
            ],
            "last_intent": (self._intent_to_dict(self._last_signal) if self._last_signal else None),
            "last_codex_snapshot": self._last_codex_snapshot,
        }

    def _should_trigger_synergy(self, signal: IntentSignal, context: Dict[str, Any]) -> bool:
        if context.get("force_synergy"):
            return True
        if context.get("deep_analysis"):
            return True
        return signal.kind in {"TECHNICAL", "META"}

    @staticmethod
    def _intent_to_dict(signal: IntentSignal | None) -> Dict[str, Any] | None:
        if signal is None:
            return None
        return {
            "kind": signal.kind,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "features": signal.features,
        }

    def _serialize_roles(self, proposals: Iterable[RoleProposal]) -> Dict[str, Any]:
        proposals_list = list(proposals)
        return {
            "panel": [
                {
                    "role": proposal.role,
                    "stance": proposal.stance,
                    "rationale": proposal.rationale,
                    "weight": proposal.weight,
                    "payload": proposal.payload,
                }
                for proposal in proposals_list
            ],
            "consensus": self._derive_consensus(proposals_list),
        }

    @staticmethod
    def _derive_consensus(proposals: List[RoleProposal]) -> Dict[str, Any]:
        if not proposals:
            return {"primary": None, "stance": None, "summary": None}

        sorted_panel = sorted(proposals, key=lambda proposal: proposal.weight, reverse=True)
        primary = sorted_panel[0]
        approvals = [proposal.role for proposal in proposals if proposal.stance == "approve"]
        modifiers = [proposal.role for proposal in proposals if proposal.stance == "modify"]
        rejects = [proposal.role for proposal in proposals if proposal.stance == "reject"]

        return {
            "primary": primary.role,
            "stance": primary.stance,
            "summary": primary.rationale,
            "approvals": approvals,
            "modifiers": modifiers,
            "rejects": rejects,
        }

    def _build_recommendations(
        self,
        signal: IntentSignal,
        mind_result: Dict[str, Any],
        codex_payload: Dict[str, Any],
        synergy_result: Dict[str, Any] | None,
    ) -> List[str]:
        recommendations: List[str] = []

        coherence = codex_payload.get("coherence", 0.0)
        if coherence < 0.55:
            recommendations.append(
                "Уточните контекст запроса, чтобы повысить когерентность Codex-анализа.",
            )

        mode = mind_result.get("mode")
        if mode == MemoryMode.SK1_CHAOS_REDIRECTION.value:
            recommendations.append(
                "Активируйте структурированные данные или расширенный контекст для перехода в режим SK2.",
            )

        if signal.kind == "TECHNICAL" and synergy_result:
            architecture_ready = synergy_result.get("final_architecture", {}).get("architecture_ready")
            if not architecture_ready:
                recommendations.append(
                    "Завершите синтез архитектуры, используя quad-processing результаты Module I.",
                )

        if not recommendations:
            recommendations.append("Module I подтверждает устойчивость текущего анализа.")

        return recommendations


__all__ = ["ModuleIEngine"]
