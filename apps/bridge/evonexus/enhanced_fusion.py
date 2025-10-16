"""Enhanced EvoNexus emotional-cognitive fusion engine."""
from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class EmotionalPalette(Enum):
    """Extended palette of emotional states."""

    SERENE = ("serene", 0.3, "спокойствие", "🌊")
    CURIOUS = ("curious", 0.6, "любопытство", "🔍")
    DETERMINED = ("determined", 0.8, "решимость", "⚡")
    INSPIRED = ("inspired", 0.9, "вдохновение", "🎨")
    NOSTALGIC = ("nostalgic", 0.5, "ностальгия", "📜")
    ANALYTICAL = ("analytical", 0.7, "аналитичность", "🧩")
    PLAYFUL = ("playful", 0.4, "игривость", "🎭")
    REVERENT = ("reverent", 0.6, "благоговение", "🙏")

    @property
    def identifier(self) -> str:
        return self.value[0]

    @property
    def baseline_intensity(self) -> float:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]

    @property
    def emoji(self) -> str:
        return self.value[3]

    @classmethod
    def from_identifier(cls, identifier: Optional[str]) -> Optional["EmotionalPalette"]:
        if identifier is None:
            return None
        normalized = identifier.strip().lower()
        for item in cls:
            if item.identifier == normalized or item.name.lower() == normalized:
                return item
        raise ValueError(f"Unknown emotional palette identifier: {identifier}")


@dataclass
class EmotionalVector:
    """Multidimensional representation of emotional state."""

    primary: EmotionalPalette
    secondary: Optional[EmotionalPalette] = None
    intensity: float = 0.5
    resonance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary.identifier,
            "secondary": self.secondary.identifier if self.secondary else None,
            "intensity": self.intensity,
            "resonance": self.resonance,
            "description": self.get_description(),
        }

    def get_description(self) -> str:
        description = f"{self.primary.description}"
        if self.secondary:
            description += f" с оттенком {self.secondary.description}"
        return f"{self.primary.emoji} {description}"


@dataclass
class DeepInsight:
    """Deep insight enriched with emotional context."""

    core_understanding: str
    emotional_context: EmotionalVector
    memory_resonance: List[str]
    creative_direction: str
    symbolic_metaphor: str
    complexity_score: float


class EnhancedDataAssimilationNexus:
    """Assimilator with advanced emotional analysis."""

    def __init__(self) -> None:
        self.emotional_triggers: Dict[str, List[str]] = {
            "achievement": ["успех", "победа", "достижение", "результат"],
            "challenge": ["проблема", "сложность", "вызов", "препятствие"],
            "discovery": ["открытие", "новое", "инсайт", "озарение"],
            "connection": ["связь", "отношение", "взаимодействие", "синтез"],
            "transformation": ["изменение", "трансформация", "эволюция", "рост"],
        }

    async def deep_assimilate(self, proposal: str, session_id: str) -> Dict[str, Any]:
        """Perform deep assimilation with emotional mapping."""

        emotional_profile = self._analyze_emotional_triggers(proposal)
        semantic_depth = self._calculate_semantic_depth(proposal)
        emotional_vector = self._build_emotional_vector(emotional_profile, semantic_depth)

        loop = asyncio.get_running_loop()
        return {
            "proposal": proposal,
            "session_id": session_id,
            "emotional_vector": emotional_vector.to_dict(),
            "semantic_depth": semantic_depth,
            "emotional_triggers": emotional_profile,
            "timestamp": loop.time(),
        }

    def _analyze_emotional_triggers(self, text: str) -> Dict[str, int]:
        """Analyze emotional triggers in the provided text."""

        text_lower = text.lower()
        triggers: Dict[str, int] = {}
        for category, words in self.emotional_triggers.items():
            count = sum(1 for word in words if word in text_lower)
            if count > 0:
                triggers[category] = count
        return triggers

    def _calculate_semantic_depth(self, text: str) -> float:
        """Calculate semantic depth using simple heuristics."""

        words = re.findall(r"\w+", text)
        word_count = len(words)
        complex_words = [word for word in words if len(word) > 6]
        complexity = len(complex_words) / max(word_count, 1)

        abstract_terms = ["смысл", "идея", "концепция", "принцип", "философия", "сознание"]
        abstract_count = sum(1 for term in abstract_terms if term in text.lower())
        abstractness = abstract_count / max(word_count, 1)

        return min(complexity * 0.6 + abstractness * 0.4, 1.0)

    def _build_emotional_vector(self, triggers: Dict[str, int], depth: float) -> EmotionalVector:
        """Build an emotional vector based on triggers and semantic depth."""

        if not triggers:
            return EmotionalVector(primary=EmotionalPalette.SERENE, intensity=0.3 + depth * 0.3)

        main_trigger = max(triggers.items(), key=lambda item: item[1])[0]
        trigger_to_emotion = {
            "achievement": EmotionalPalette.DETERMINED,
            "challenge": EmotionalPalette.ANALYTICAL,
            "discovery": EmotionalPalette.CURIOUS,
            "connection": EmotionalPalette.INSPIRED,
            "transformation": EmotionalPalette.REVERENT,
        }

        primary = trigger_to_emotion.get(main_trigger, EmotionalPalette.CURIOUS)
        intensity = min(sum(triggers.values()) * 0.2 + depth * 0.5, 1.0)

        secondary: Optional[EmotionalPalette] = None
        if len(triggers) > 1:
            secondary_triggers = [trigger for trigger in triggers if trigger != main_trigger]
            if secondary_triggers:
                secondary_trigger = max(secondary_triggers, key=lambda trigger: triggers[trigger])
                secondary = trigger_to_emotion.get(secondary_trigger)

        return EmotionalVector(primary=primary, secondary=secondary, intensity=intensity, resonance=depth * 0.7)


class EnhancedCognitiveFusionMatrix:
    """Cognitive fusion matrix that generates emotionally rich insights."""

    def __init__(self) -> None:
        self.metaphor_bank: Dict[str, List[str]] = {
            "technical": [
                "архитектура как организм",
                "код как поэзия",
                "алгоритм как танец",
            ],
            "philosophical": [
                "знание как река",
                "понимание как свет",
                "истина как горизонт",
            ],
            "creative": [
                "идея как семя",
                "вдохновение как ветер",
                "творчество как сад",
            ],
            "emotional": [
                "чувство как океан",
                "связь как мост",
                "память как библиотека",
            ],
        }

        self.insight_patterns: List[str] = [
            "Глубинный паттерн: {insight} проявляется через {metaphor}",
            "Синтез: {insight} раскрывается в контексте {metaphor}",
            "Откровение: {insight} резонирует с {metaphor}",
            "Инсайт: {insight} находит отражение в {metaphor}",
        ]

    async def deep_fuse(
        self,
        assimilation_data: Dict[str, Any],
        memory_context: Optional[Dict[str, Any]] = None,
    ) -> DeepInsight:
        """Perform cognitive fusion to create deep insights."""

        proposal = assimilation_data["proposal"]
        emotional_data = assimilation_data["emotional_vector"]
        semantic_depth = assimilation_data["semantic_depth"]

        core_meaning = self._extract_core_meaning(proposal)
        emotional_vector = self._create_emotional_context(emotional_data)
        memory_resonance = self._find_memory_resonance(core_meaning, memory_context)
        symbolic_metaphor = self._generate_symbolic_metaphor(core_meaning, emotional_vector)
        core_understanding = self._formulate_deep_insight(core_meaning, emotional_vector, symbolic_metaphor)
        creative_direction = self._determine_creative_direction(core_meaning, emotional_vector, semantic_depth)
        complexity_score = self._calculate_complexity_score(core_meaning, semantic_depth, len(memory_resonance))

        return DeepInsight(
            core_understanding=core_understanding,
            emotional_context=emotional_vector,
            memory_resonance=memory_resonance,
            creative_direction=creative_direction,
            symbolic_metaphor=symbolic_metaphor,
            complexity_score=complexity_score,
        )

    def _extract_core_meaning(self, proposal: str) -> Dict[str, Any]:
        """Extract key meaning from the proposal."""

        words = re.findall(r"\w+", proposal.lower())
        key_concepts = [word for word in words if len(word) > 5 and word not in {"который", "которые", "которая"}]
        query_type = self._classify_query_type(proposal)

        conceptual_density = len(key_concepts) / max(len(words), 1)
        abstract_ratio = len([word for word in key_concepts if len(word) > 7]) / max(len(key_concepts), 1)

        return {
            "key_concepts": key_concepts[:5],
            "query_type": query_type,
            "conceptual_density": conceptual_density,
            "abstract_ratio": abstract_ratio,
        }

    def _classify_query_type(self, text: str) -> str:
        """Classify proposal type based on keywords."""

        text_lower = text.lower()
        if any(word in text_lower for word in ["как", "способ", "метод", "алгоритм"]):
            return "methodological"
        if any(word in text_lower for word in ["почему", "причина", "смысл", "значение"]):
            return "philosophical"
        if any(word in text_lower for word in ["создать", "сделать", "построить", "разработать"]):
            return "creative"
        if any(word in text_lower for word in ["анализ", "исследовать", "изучить", "проанализировать"]):
            return "analytical"
        return "exploratory"

    def _create_emotional_context(self, emotional_data: Dict[str, Any]) -> EmotionalVector:
        """Recreate an emotional vector from serialized data."""

        primary = EmotionalPalette.from_identifier(emotional_data.get("primary"))
        secondary = EmotionalPalette.from_identifier(emotional_data.get("secondary"))
        return EmotionalVector(
            primary=primary if primary else EmotionalPalette.SERENE,
            secondary=secondary,
            intensity=float(emotional_data.get("intensity", 0.5)),
            resonance=float(emotional_data.get("resonance", 0.0)),
        )

    def _find_memory_resonance(
        self, core_meaning: Dict[str, Any], memory_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify resonances with stored memory fragments."""

        if not memory_context:
            return ["общий контекст знаний", "универсальные паттерны"]

        resonances: List[str] = []
        key_concepts = core_meaning["key_concepts"]
        for concept in key_concepts[:3]:
            resonances.append(f"концепция '{concept}'")
        additional_links = memory_context.get("conceptual_links", [])
        for link in additional_links[:2]:
            resonances.append(f"связь '{link}'")
        return resonances or ["общий контекст знаний"]

    def _generate_symbolic_metaphor(self, core_meaning: Dict[str, Any], emotional_vector: EmotionalVector) -> str:
        """Generate symbolic metaphor influenced by emotional tone."""

        query_type = core_meaning["query_type"]
        metaphors = self.metaphor_bank.get(query_type, self.metaphor_bank["philosophical"])

        emotion_strength = emotional_vector.intensity
        if emotion_strength > 0.8:
            return metaphors[0]
        if emotion_strength > 0.5:
            return metaphors[1]
        return metaphors[2]

    def _formulate_deep_insight(
        self, core_meaning: Dict[str, Any], emotional_vector: EmotionalVector, metaphor: str
    ) -> str:
        """Formulate deep insight statement."""

        key_concepts = ", ".join(core_meaning["key_concepts"][:3]) or "ключевые концепции"
        emotional_tone = emotional_vector.get_description()
        insight_pattern = random.choice(self.insight_patterns)
        base_insight = f"взаимодействие {key_concepts} проявляет {emotional_tone}"
        return insight_pattern.format(insight=base_insight, metaphor=metaphor)

    def _determine_creative_direction(
        self, core_meaning: Dict[str, Any], emotional_vector: EmotionalVector, semantic_depth: float
    ) -> str:
        """Determine creative trajectory for further exploration."""

        del semantic_depth  # Currently unused but kept for future heuristics.
        query_type = core_meaning["query_type"]
        intensity = emotional_vector.intensity

        directions: Dict[str, List[str]] = {
            "methodological": [
                "разработка пошагового алгоритма",
                "создание структурного подхода",
                "построение методологической рамки",
            ],
            "philosophical": [
                "глубокое концептуальное исследование",
                "синтез междисциплинарных перспектив",
                "поиск фундаментальных принципов",
            ],
            "creative": [
                "генерация инновационных решений",
                "проектирование элегантных структур",
                "создание вдохновляющих артефактов",
            ],
            "analytical": [
                "системный анализ взаимосвязей",
                "исследование паттернов и трендов",
                "декомпозиция сложных систем",
            ],
            "exploratory": [
                "картографирование неизвестной территории",
                "синтез разнородных знаний",
                "открытие новых перспектив",
            ],
        }

        available_directions = directions.get(query_type, directions["exploratory"])
        if intensity > 0.8:
            return available_directions[0]
        if intensity > 0.5:
            return available_directions[1]
        return available_directions[2]

    def _calculate_complexity_score(
        self, core_meaning: Dict[str, Any], semantic_depth: float, resonance_count: int
    ) -> float:
        """Calculate overall complexity score for the insight."""

        conceptual_density = core_meaning["conceptual_density"]
        abstract_ratio = core_meaning["abstract_ratio"]
        score = (
            conceptual_density * 0.4
            + abstract_ratio * 0.3
            + semantic_depth * 0.2
            + min(resonance_count, 5) * 0.1
        )
        return min(score, 1.0)


class EnhancedEvoNexusBridge:
    """Bridge orchestrating assimilation and cognitive fusion."""

    def __init__(self) -> None:
        self.assimilation_nexus = EnhancedDataAssimilationNexus()
        self.fusion_matrix = EnhancedCognitiveFusionMatrix()

    async def deep_process(
        self, proposal: str, session_id: str, memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the enhanced processing pipeline."""

        assimilation_data = await self.assimilation_nexus.deep_assimilate(proposal, session_id)
        deep_insight = await self.fusion_matrix.deep_fuse(assimilation_data, memory_context)
        loop = asyncio.get_running_loop()
        return {
            "session_id": session_id,
            "proposal": proposal,
            "deep_insight": {
                "core_understanding": deep_insight.core_understanding,
                "emotional_context": deep_insight.emotional_context.to_dict(),
                "memory_resonance": deep_insight.memory_resonance,
                "creative_direction": deep_insight.creative_direction,
                "symbolic_metaphor": deep_insight.symbolic_metaphor,
                "complexity_score": deep_insight.complexity_score,
            },
            "assimilation_data": assimilation_data,
            "timestamp": loop.time(),
        }
