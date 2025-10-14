"""Quantum Context Analyzer module for EvoCodex."""

from __future__ import annotations

import asyncio
import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional

from apps.core.context.models import (
    AffectResult,
    IntentResult,
    MemoryLedgerProtocol,
    MemoryResult,
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _tokenize(query: str) -> List[str]:
    """Tokenise the query into lowercase word-like fragments."""

    return re.findall(r"[\w-]+", query.lower())


def _score_keywords(tokens: Iterable[str], keywords: Iterable[str]) -> float:
    """Compute a simple matching score between tokens and keywords."""

    token_list = list(tokens)
    if not token_list:
        return 0.0
    keywords_set = set(keywords)
    matches = sum(1 for token in token_list if token in keywords_set)
    return matches / len(token_list)


# ---------------------------------------------------------------------------
# Lightweight heuristic models
# ---------------------------------------------------------------------------


class IntentModel:
    """Intent classifier used by the analyzer."""

    _INTENT_KEYWORDS = {
        "urgent": {"срочно", "urgent", "немедленно", "emergency"},
        "technical": {
            "архитектура",
            "architecture",
            "code",
            "ошибка",
            "bug",
            "system",
        },
        "philosophical": {"смысл", "meaning", "why", "philosophy", "духов", "жизнь"},
        "creative": {"идея", "concept", "imagine", "творч", "design"},
        "casual": {"привет", "hello", "как", "напомни", "tell"},
    }

    async def predict(self, query: str) -> IntentResult:
        """Return a deterministic intent prediction derived from heuristics."""

        tokens = _tokenize(query)
        await asyncio.sleep(0.01)

        urgency_score = _score_keywords(tokens, self._INTENT_KEYWORDS["urgent"])
        punctuation_boost = min(query.count("!"), 3) * 0.12
        urgency = min(1.0, 0.25 + 0.55 * urgency_score + punctuation_boost)

        intent_type = "casual"
        highest_score = 0.0
        for label, keywords in self._INTENT_KEYWORDS.items():
            score = _score_keywords(tokens, keywords)
            if score > highest_score:
                highest_score = score
                intent_type = label

        if urgency >= 0.75:
            intent_type = "urgent"

        confidence = min(0.95, 0.65 + highest_score * 0.3 + urgency_score * 0.2)
        return IntentResult(urgency=urgency, type=intent_type, confidence=confidence)


class SoulAffectEncoder:
    """Encoder modelling affective signals."""

    _EMOTION_KEYWORDS = {
        "fear": {"страх", "fear", "опас", "паник"},
        "melancholy": {"грусть", "melan", "lonely", "пустоту"},
        "joy": {"рад", "joy", "успех", "happy"},
        "calm": {"спокой", "calm", "мир"},
        "curiosity": {"интерес", "curious", "почему", "как"},
        "determination": {"фокус", "достиг", "решим", "намерен"},
    }

    async def encode(self, query: str) -> AffectResult:
        """Return a deterministic affective encoding for the query."""

        tokens = _tokenize(query)
        await asyncio.sleep(0.01)

        dominant_emotion = "calm"
        dominant_score = 0.0
        for emotion, keywords in self._EMOTION_KEYWORDS.items():
            score = _score_keywords(tokens, keywords)
            if score > dominant_score:
                dominant_emotion = emotion
                dominant_score = score

        resonance = min(1.0, 0.35 + dominant_score * 0.55)
        intensity = min(1.0, 0.45 + dominant_score * 0.4 + min(len(query) / 200, 0.15))

        return AffectResult(
            soul_resonance=resonance,
            emotion=dominant_emotion,
            intensity=intensity,
        )


class DigitalSoulLedger:
    """Asynchronous facade for memory lookup operations."""

    async def find_related_fragments(
        self, query: str, threshold: float = 0.85
    ) -> MemoryResult:
        """Return deterministic fragments related to the query."""

        tokens = [token for token in _tokenize(query) if len(token) > 3]
        await asyncio.sleep(0.01)
        if not tokens:
            return MemoryResult(has_strong_links=False, fragments=[], relevance_score=0.0)

        scores: List[float] = []
        fragments: List[str] = []
        details: List[Dict[str, Any]] = []
        for token in tokens[:3]:
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()[:16]
            fragments.append(f"0x{digest}")
            score = min(1.0, 0.4 + len(token) / 20)
            scores.append(score)
            details.append({"token": token, "score": round(score, 3)})

        average_score = sum(scores) / len(scores)
        has_links = average_score >= max(0.2, threshold - 0.5)
        relevance_score = min(1.0, average_score)
        return MemoryResult(
            has_strong_links=has_links,
            fragments=fragments,
            relevance_score=relevance_score,
            details=details,
        )


# ---------------------------------------------------------------------------
# Pipeline primitives
# ---------------------------------------------------------------------------


class AGIEngine:
    """Mock AGI engine used in processing pipelines."""

    async def process(self, context: Dict[str, Any]) -> str:
        """Simulate AGI processing of the provided context."""

        await asyncio.sleep(0.2)
        urgency = context.get("intent", {}).get("urgency", 0.5)
        return f"AGI анализ завершен (срочность: {urgency:.2f})"


class SoulLedger:
    """Auxiliary class adding spiritual flavour to responses."""

    async def add_context(self, data: str) -> str:
        """Return an enriched context string."""

        await asyncio.sleep(0.15)
        return f"Духовный контекст: {data}"

    async def retrieve(self, context: Dict[str, Any]) -> str:
        """Retrieve soul context from the provided context."""

        await asyncio.sleep(0.15)
        emotion = context.get("affect", {}).get("emotion", "neutral")
        return f"Извлечение души для эмоции: {emotion}"


class RoleAdapter:
    """Role adapter that combines AGI and soul outputs."""

    async def wrap(self, agi_data: str, soul_data: str) -> str:
        """Wrap the AGI and soul outputs into a single response."""

        await asyncio.sleep(0.1)
        return f"🤖 {agi_data} | 🌌 {soul_data}"

    async def adapt(self, context: Dict[str, Any]) -> str:
        """Return a textual representation of role adaptation."""

        await asyncio.sleep(0.1)
        fragments = context.get("memory", {}).get("fragments", [])
        return f"Адаптация роли на основе {len(fragments)} фрагментов памяти"


agi_engine = AGIEngine()
soul_ledger = SoulLedger()
role_adapter = RoleAdapter()


# ---------------------------------------------------------------------------
# Analyzer orchestration
# ---------------------------------------------------------------------------


class QuantumContextAnalyzer:
    """Main entry-point for context analysis inside EvoCodex."""

    def __init__(
        self,
        query: str,
        *,
        intent_model: IntentModel | None = None,
        soul_encoder: SoulAffectEncoder | None = None,
        memory_ledger: Optional[MemoryLedgerProtocol] = None,
    ) -> None:
        self.query = query
        self.context_layers: Dict[str, Any] = {}
        self.priority_path: str | None = None
        self._intent_model = intent_model or IntentModel()
        self._soul_encoder = soul_encoder or SoulAffectEncoder()
        self._ledger: MemoryLedgerProtocol = memory_ledger or DigitalSoulLedger()

    async def analyze(self) -> Dict[str, Any]:
        """Perform asynchronous context analysis across all layers."""

        intent_task = asyncio.create_task(self._intent_model.predict(self.query))
        affect_task = asyncio.create_task(self._soul_encoder.encode(self.query))
        memory_task = asyncio.create_task(self._ledger.find_related_fragments(self.query))

        intent_result, affect_result, memory_result = await asyncio.gather(
            intent_task, affect_task, memory_task
        )

        self.context_layers = {
            "intent": intent_result.to_dict(),
            "affect": affect_result.to_dict(),
            "memory": memory_result.to_dict(),
        }
        self._determine_priority_path()
        return self.context_layers

    def _determine_priority_path(self) -> None:
        """Determine the processing priority path from the context."""

        urgency = self.context_layers.get("intent", {}).get("urgency", 0.0)
        soul_resonance = self.context_layers.get("affect", {}).get("soul_resonance", 0.0)
        has_links = self.context_layers.get("memory", {}).get("has_strong_links", False)

        if urgency > 0.7:
            self.priority_path = "AGI"
        elif soul_resonance > 0.8:
            self.priority_path = "SOUL"
        elif has_links:
            self.priority_path = "ROLE"
        else:
            self.priority_path = "HYBRID"


async def agi_first_pipeline(context: Dict[str, Any]) -> str:
    """Pipeline prioritising AGI processing."""

    agi_result = await agi_engine.process(context)
    soul_layer = await soul_ledger.add_context(agi_result)
    return await role_adapter.wrap(agi_result, soul_layer)


async def soul_first_pipeline(context: Dict[str, Any]) -> str:
    """Pipeline prioritising soul retrieval."""

    soul_data = await soul_ledger.retrieve(context)
    agi_result = await agi_engine.process(context)
    return await role_adapter.wrap(agi_result, soul_data)


async def role_first_pipeline(context: Dict[str, Any]) -> str:
    """Pipeline prioritising role adaptation."""

    role_data = await role_adapter.adapt(context)
    agi_result = await agi_engine.process(context)
    soul_layer = await soul_ledger.add_context(agi_result)
    wrapped = await role_adapter.wrap(agi_result, soul_layer)
    return f"{role_data} + {wrapped}"


async def hybrid_pipeline(context: Dict[str, Any]) -> str:
    """Hybrid pipeline combining all components concurrently."""

    agi_task = asyncio.create_task(agi_engine.process(context))
    soul_task = asyncio.create_task(soul_ledger.retrieve(context))
    role_task = asyncio.create_task(role_adapter.adapt(context))

    agi_result, soul_data, role_data = await asyncio.gather(agi_task, soul_task, role_task)
    return f"Гибридный синтез: [{agi_result}] + [{soul_data}] + [{role_data}]"


def format_response(response: str, context: Dict[str, Any]) -> str:
    """Return a formatted response that includes contextual metadata."""

    intent = context.get("intent", {})
    affect = context.get("affect", {})
    memory = context.get("memory", {})

    return (
        "--- QUANTUM CONTEXT RESPONSE ---\n"
        f"Путь: {context.get('priority_path', 'UNKNOWN')}\n"
        f"Срочность: {intent.get('urgency', 0.0):.2f}\n"
        f"Душевный резонанс: {affect.get('soul_resonance', 0.0):.2f}\n"
        f"Фрагменты памяти: {memory.get('fragments', [])}\n\n"
        f"Ответ:\n{response}\n"
        "-------------------------------"
    )


async def analyze_and_respond(query: str) -> str:
    """Analyse the query and produce a formatted response."""

    analyzer = QuantumContextAnalyzer(query)
    context = await analyzer.analyze()
    context["priority_path"] = analyzer.priority_path

    pipelines = {
        "AGI": agi_first_pipeline,
        "SOUL": soul_first_pipeline,
        "ROLE": role_first_pipeline,
        "HYBRID": hybrid_pipeline,
    }
    pipeline = pipelines[analyzer.priority_path]
    response = await pipeline(context)
    return format_response(response, context)


__all__ = [
    "QuantumContextAnalyzer",
    "analyze_and_respond",
    "agi_first_pipeline",
    "soul_first_pipeline",
    "role_first_pipeline",
    "hybrid_pipeline",
]
