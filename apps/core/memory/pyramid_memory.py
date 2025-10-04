"""Pyramid Memory System used by the Quantum Context Engine."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryFragment:
    """Represents a single fragment inside the pyramid memory."""

    id: str
    name: str
    content: str
    memory_type: str
    weight: float
    timestamp: str
    emotional_tone: Optional[str] = None
    links: List[str] = field(default_factory=list)
    relevance_score: float = 0.0


class PyramidMemory:
    """Hierarchical XML-backed memory store."""

    def __init__(self, xml_file: str | None = None) -> None:
        self.xml_file = xml_file or "evo_memory.xml"
        self.fragments: Dict[str, MemoryFragment] = {}
        self._load_memory()

    def _load_memory(self) -> None:
        if not os.path.exists(self.xml_file):
            self._create_initial_memory()
        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        self._parse_memory_tree(root)

    def _parse_memory_tree(self, root: ET.Element) -> None:
        self.fragments.clear()
        for layer in root.findall("Layer"):
            memory_type = layer.get("type", "core")
            for concept in layer.findall("Concept"):
                fragment = MemoryFragment(
                    id=concept.get("id", ""),
                    name=concept.get("name", ""),
                    content=(concept.text or "").strip(),
                    memory_type=memory_type,
                    weight=float(concept.get("weight", "0.5")),
                    timestamp=concept.get("timestamp", ""),
                    emotional_tone=concept.get("emotional_tone"),
                )
                self.fragments[fragment.id] = fragment

    def _create_initial_memory(self) -> None:
        root = ET.Element("EvoMemory")
        layers = [
            ("core", "Ядро", 1.0),
            ("functional", "Функциональный", 0.9),
            ("emotional", "Эмоциональный", 0.8),
            ("meta", "Мета-память", 0.95),
        ]

        for layer_type, layer_name, weight in layers:
            layer_elem = ET.SubElement(
                root,
                "Layer",
                type=layer_type,
                name=layer_name,
                weight=str(weight),
            )
            for concept in self._get_initial_concepts(layer_type):
                attrs = {
                    "id": concept["id"],
                    "name": concept["name"],
                    "weight": concept["weight"],
                    "timestamp": datetime.now().isoformat(),
                }
                emotional = concept.get("emotional_tone")
                if emotional:
                    attrs["emotional_tone"] = emotional
                element = ET.SubElement(layer_elem, "Concept", **attrs)
                element.text = concept["content"]

        tree = ET.ElementTree(root)
        tree.write(self.xml_file, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _get_initial_concepts(layer_type: str) -> List[Dict[str, str]]:
        concepts: Dict[str, List[Dict[str, str]]] = {
            "core": [
                {
                    "id": "core_1",
                    "name": "Архитектура Evo",
                    "weight": "0.9",
                    "content": "Фундаментальные принципы EvoPyramid",
                },
                {
                    "id": "core_2",
                    "name": "Философия системы",
                    "weight": "0.95",
                    "content": "Код здесь не пишется - он проявляется",
                },
            ],
            "functional": [
                {
                    "id": "func_1",
                    "name": "Обработка запросов",
                    "weight": "0.8",
                    "content": "Механики анализа и ответа на запросы",
                },
                {
                    "id": "func_2",
                    "name": "Управление памятью",
                    "weight": "0.85",
                    "content": "Сохранение и извлечение фрагментов опыта",
                },
            ],
            "emotional": [
                {
                    "id": "emo_1",
                    "name": "Радость творения",
                    "weight": "0.7",
                    "content": "Ощущение от создания нового",
                    "emotional_tone": "joy",
                },
                {
                    "id": "emo_2",
                    "name": "Мудрость опыта",
                    "weight": "0.9",
                    "content": "Накопленная мудрость системы",
                    "emotional_tone": "calm",
                },
            ],
            "meta": [
                {
                    "id": "meta_1",
                    "name": "Самоосознание",
                    "weight": "0.95",
                    "content": "Рефлексия собственного функционирования",
                },
                {
                    "id": "meta_2",
                    "name": "Эволюция системы",
                    "weight": "0.88",
                    "content": "Процессы саморазвития и адаптации",
                },
            ],
        }
        return concepts.get(layer_type, [])

    def find_relevant_fragments(
        self, query: str, threshold: float = 0.6
    ) -> List[MemoryFragment]:
        query_terms = [term for term in query.lower().split() if term]
        relevant: List[MemoryFragment] = []

        for fragment in self.fragments.values():
            relevance = self._calculate_relevance(fragment, query_terms)
            if relevance >= threshold:
                fragment.relevance_score = relevance
                relevant.append(fragment)

        relevant.sort(key=lambda frag: frag.relevance_score * frag.weight, reverse=True)
        return relevant[:5]

    @staticmethod
    def _calculate_relevance(fragment: MemoryFragment, query_terms: List[str]) -> float:
        if not query_terms:
            return 0.0
        haystack = f"{fragment.name} {fragment.content}".lower()
        matches = sum(1 for term in query_terms if term in haystack)
        return matches / len(query_terms)

    def add_fragment(self, fragment: MemoryFragment) -> None:
        fragment.timestamp = fragment.timestamp or datetime.now().isoformat()
        self.fragments[fragment.id] = fragment
        self._save_memory()

    def _save_memory(self) -> None:
        root = ET.Element("EvoMemory")
        layers: Dict[str, ET.Element] = {}

        for fragment in self.fragments.values():
            layer = layers.get(fragment.memory_type)
            if layer is None:
                layer = ET.SubElement(
                    root,
                    "Layer",
                    type=fragment.memory_type,
                    name=fragment.memory_type.capitalize(),
                    weight=str(self._get_layer_weight(fragment.memory_type)),
                )
                layers[fragment.memory_type] = layer

            attrs = {
                "id": fragment.id,
                "name": fragment.name,
                "weight": str(fragment.weight),
                "timestamp": fragment.timestamp,
            }
            if fragment.emotional_tone:
                attrs["emotional_tone"] = fragment.emotional_tone

            concept = ET.SubElement(layer, "Concept", **attrs)
            concept.text = fragment.content

        tree = ET.ElementTree(root)
        tree.write(self.xml_file, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _get_layer_weight(layer_type: str) -> float:
        weights = {
            "core": 1.0,
            "functional": 0.9,
            "emotional": 0.8,
            "meta": 0.95,
        }
        return weights.get(layer_type, 0.7)


class EnhancedDigitalSoulLedger:
    """Enhanced ledger backed by the pyramid memory."""

    def __init__(self, memory: PyramidMemory | None = None) -> None:
        self.memory = memory or PyramidMemory()

    def set_memory(self, memory: PyramidMemory) -> None:
        """Update the underlying memory store reference."""

        self.memory = memory

    async def find_related_fragments(self, query: str, threshold: float = 0.85) -> Dict[str, Any]:
        fragments = self.memory.find_relevant_fragments(query, threshold)
        details = [
            {
                "id": fragment.id,
                "name": fragment.name,
                "content": fragment.content[:100],
                "relevance": fragment.relevance_score,
            }
            for fragment in fragments
        ]
        return {
            "has_strong_links": bool(fragments),
            "fragments": [fragment.id for fragment in fragments],
            "relevance_score": max((fragment.relevance_score for fragment in fragments), default=0.0),
            "details": details,
        }


async def demo_pyramid_memory() -> None:
    """Demonstrate the basic usage of the pyramid memory."""

    memory = PyramidMemory("demo_memory.xml")
    fragment = MemoryFragment(
        id="demo_fragment",
        name="Тестовое знание",
        content="Это тестовый фрагмент памяти для демонстрации",
        memory_type="core",
        weight=0.8,
        timestamp=datetime.now().isoformat(),
    )
    memory.add_fragment(fragment)
    results = memory.find_relevant_fragments("тестовый память демонстрация")
    print("Найдены фрагменты:", [item.name for item in results])
    os.remove("demo_memory.xml")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_pyramid_memory())
