from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.core.integration.context_engine import get_context_engine


# ---------- Assimilation ----------
@dataclass
class AssimilationBundle:
    proposal: str
    session_id: str
    context: Dict[str, Any]  # intent/affect/memory + priority_path


class DataAssimilationNexus:
    """
    Принимает мультимодальные данные/предложения, прогоняет через контекстный движок
    и возвращает "пакет" для дальнейшего синтеза.
    """

    async def assimilate(self, proposal: str, session_id: str) -> AssimilationBundle:
        engine = get_context_engine()
        analyzed = await engine.process_query(proposal)
        if not analyzed.get("success"):
            # падать не будем — вернём максимально полезную структуру
            context = {
                "intent": {"urgency": 0.5, "type": "casual", "confidence": 0.7},
                "affect": {"emotion": "calm", "intensity": 0.6, "soul_resonance": 0.5},
                "memory": {"has_strong_links": False, "fragments": [], "relevance_score": 0.3},
                "priority_path": "HYBRID",
            }
        else:
            context = analyzed["context"]
            context["priority_path"] = analyzed.get("priority_path", "HYBRID")

        return AssimilationBundle(proposal=proposal, session_id=session_id, context=context)


# ---------- Fusion ----------
@dataclass
class FusionResult:
    insight: str
    creative_output: str
    signals: Dict[str, Any]
    density: float  # условная метрика «насыщенности»


class CognitiveFusionMatrix:
    """
    Синтезирует инсайт (что важно) и творческий выход (как действовать/что сгенерировать).
    Подмешивает эмоции и память для "тона" ответа.
    """

    async def fuse(self, bundle: AssimilationBundle) -> FusionResult:
        ctx = bundle.context
        intent = ctx.get("intent", {})
        affect = ctx.get("affect", {})
        memory = ctx.get("memory", {})

        urgency = float(intent.get("urgency", 0.5))
        intent_type = intent.get("type", "casual")
        emotion = affect.get("emotion", "calm")
        intensity = float(affect.get("intensity", 0.6))
        has_links = bool(memory.get("has_strong_links", False))
        fragments = memory.get("fragments", [])

        # простая «тональная» формула инсайта
        tone = "решительно" if intensity > 0.75 else "взвешенно"
        insight = (
            f"Инсайт: {tone} обработать предложение '{bundle.proposal}' "
            f"(intent={intent_type}, urgency={urgency:.2f}, emotion={emotion}). "
            + ("Обнаружены сильные связи в памяти; используем их. " if has_links else "Сильных связей в памяти нет. ")
        )

        # креативный выход — мини-план
        steps = [
            f"- Пройти приоритетный путь: {ctx.get('priority_path', 'HYBRID')}",
            "- Уточнить ключевые роли и точки синергии",
            "- Подготовить черновик кода/структуры под модульные изменения",
            "- Сохранить артефакт в общий пул и запустить консенсус",
        ]
        if has_links and fragments:
            steps.insert(1, f"- Подтянуть фрагменты памяти: {', '.join(fragments[:3])}")
        creative_output = "План действий:\n" + "\n".join(steps)

        # «насыщенность» по простому правилу
        density = urgency + (0.2 if has_links else 0.0) + (0.1 if intensity > 0.7 else 0.0)

        signals = {
            "priority_path": ctx.get("priority_path", "HYBRID"),
            "emotion": emotion,
            "intent_type": intent_type,
            "urgency": urgency,
            "has_memory_links": has_links,
        }
        return FusionResult(
            insight=insight,
            creative_output=creative_output,
            signals=signals,
            density=float(density),
        )


# ---------- Consensus ----------
@dataclass
class Vote:
    core: str
    weight: float
    decision: str  # approve / modify / reject / evolve


class ConsensusEngine:
    """
    Вычисляет «душевный консенсус» среди ядер.
    """

    def __init__(self, role_weights: Optional[Dict[str, float]] = None):
        self.role_weights = role_weights or {
            "EvoKernel": 1.0,
            "ExEvo": 0.85,
            "Evo24": 0.90,
            "Codex": 0.95,
        }
        self.threshold_gold = 0.75
        self.threshold_platinum = 0.9

    def _core_vote(self, core: str, fusion: FusionResult, rng: random.Random) -> str:
        urgency = fusion.signals.get("urgency", 0.5)
        density = fusion.density
        emotion = fusion.signals.get("emotion", "calm")

        # простая эвристика
        score = urgency + (0.2 if density > 1.2 else 0.0)
        if emotion == "fear":
            score -= 0.1
        if emotion == "determination":
            score += 0.1

        # шум/индивидуальность ядра
        score += rng.uniform(-0.05, 0.05)

        if score > 1.0:
            return "evolve"
        if score > 0.7:
            return "approve"
        if score > 0.45:
            return "modify"
        return "reject"

    def decide(self, fusion: FusionResult, seed: Optional[int] = None) -> Dict[str, Any]:
        rng = random.Random(seed)
        votes: List[Vote] = []
        for core, weight in self.role_weights.items():
            decision = self._core_vote(core, fusion, rng)
            votes.append(Vote(core=core, weight=weight, decision=decision))

        # агрегируем
        weight_sum = sum(v.weight for v in votes)
        weighted = 0.0
        for vote in votes:
            if vote.decision == "evolve":
                weighted += vote.weight * 1.1
            elif vote.decision == "approve":
                weighted += vote.weight * 1.0
            elif vote.decision == "modify":
                weighted += vote.weight * 0.5
            # reject -> 0

        consensus_score = weighted / max(weight_sum, 1e-6)
        if consensus_score >= self.threshold_platinum:
            state = "platinum"
            decision = "evolve"
        elif consensus_score >= self.threshold_gold:
            state = "gold"
            decision = "approve"
        else:
            state = "standard"
            decision = "modify" if consensus_score >= 0.5 else "reject"

        return {
            "consensus": round(consensus_score, 3),
            "state": state,
            "decision": decision,
            "votes": [vote.__dict__ for vote in votes],
        }


# ---------- Orchestrator ----------
class EvoNexusBridge:
    """
    Полный цикл: assimilate -> fuse -> consensus.
    """

    def __init__(self) -> None:
        self.assim = DataAssimilationNexus()
        self.fusion = CognitiveFusionMatrix()
        self.consensus = ConsensusEngine()
        self.artifacts_dir = (
            os.environ.get("EVODIR")
            or ("./local_EVO" if not os.path.exists("/storage/emulated/0") else "/storage/emulated/0/Download/EVO")
        )
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(os.path.join(self.artifacts_dir, "nexus_logs"), exist_ok=True)

    async def run(self, proposal: str, session_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
        bundle = await self.assim.assimilate(proposal, session_id)
        fused = await self.fusion.fuse(bundle)
        verdict = self.consensus.decide(fused, seed=seed)

        output = {
            "session_id": session_id,
            "proposal": proposal,
            "context": bundle.context,
            "fusion": fused.__dict__,
            "verdict": verdict,
            "ts": int(time.time()),
        }
        self._persist(output)
        return output

    def _persist(self, data: Dict[str, Any]) -> None:
        path = os.path.join(self.artifacts_dir, "nexus_logs", f"nexus_{data['ts']}.json")
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception:
            # не блокируем основной поток из-за ошибок записи
            pass
