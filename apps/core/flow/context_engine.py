"""Адаптер для интеграционного контекстного движка."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.core.integration.context_engine import EvoCodexContextEngine, get_context_engine
from apps.core.memory.memory_manager import Memory


@dataclass(slots=True)
class QuantumContextResult:
    """Результат обработки QuantumContext."""

    design: Dict[str, Any]
    coherence: float
    trace_id: str
    response: str
    processing_time: float
    agents_activated: List[str]
    raw_context: Dict[str, Any]

    @property
    def result(self) -> Dict[str, Any]:
        """Упрощённый доступ к итоговому контексту."""

        return {
            "response": self.response,
            "priority_path": self.design["priority_path"],
            "intent": self.raw_context.get("intent", {}),
            "affect": self.raw_context.get("affect", {}),
            "memory": self.raw_context.get("memory", {}),
        }


class QuantumContext:
    """Фасад над EvoCodexContextEngine с расширенной телеметрией."""

    _engine: Optional[EvoCodexContextEngine] = None

    @classmethod
    def _get_engine(cls) -> EvoCodexContextEngine:
        if cls._engine is None:
            cls._engine = get_context_engine()
        return cls._engine

    @classmethod
    async def process(
        cls, intent: str, context: Optional[Dict[str, Any]] = None
    ) -> QuantumContextResult:
        """Запуск анализа и генерации архитектурного дизайна."""

        engine = cls._get_engine()
        result = await engine.process_query(intent, context)
        if not result.get("success", False):
            raise RuntimeError(result.get("error", "context processing failed"))

        raw_context = result["context"]
        priority_path = result["priority_path"]
        trace_id = uuid.uuid4().hex
        agents = cls._agents_for_path(priority_path)
        coherence = cls._estimate_coherence(raw_context, priority_path)

        design = {
            "summary": result["response"],
            "priority_path": priority_path,
            "intent": raw_context.get("intent", {}),
            "affect": raw_context.get("affect", {}),
            "memory": raw_context.get("memory", {}),
            "processing_time": result["processing_time"],
        }

        await Memory.append_history(
            {
                "trace_id": trace_id,
                "priority_path": priority_path,
                "coherence": coherence,
            }
        )

        return QuantumContextResult(
            design=design,
            coherence=coherence,
            trace_id=trace_id,
            response=result["response"],
            processing_time=result["processing_time"],
            agents_activated=agents,
            raw_context=raw_context,
        )

    @staticmethod
    def _agents_for_path(priority_path: str) -> List[str]:
        mapping = {
            "AGI": ["Soul", "Trailblazer"],
            "SOUL": ["Soul"],
            "ROLE": ["Trailblazer"],
            "HYBRID": ["Soul", "Trailblazer", "Provocateur"],
        }
        return mapping.get(priority_path, ["Soul"])

    @staticmethod
    def _estimate_coherence(context: Dict[str, Any], priority_path: str) -> float:
        intent = context.get("intent", {})
        affect = context.get("affect", {})
        memory = context.get("memory", {})
        urgency = float(intent.get("urgency", 0.0))
        resonance = float(affect.get("soul_resonance", 0.0))
        memory_score = float(memory.get("relevance_score", 0.0))

        base = (urgency + resonance + memory_score) / 3 if priority_path != "HYBRID" else (
            urgency * 0.3 + resonance * 0.3 + memory_score * 0.4
        )
        return round(min(1.0, max(0.0, base)), 3)


__all__ = ["QuantumContext", "QuantumContextResult", "get_context_engine"]
