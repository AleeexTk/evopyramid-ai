"""Utilities for analyzing EvoMethod_SK memory JSON structures."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BlockMetrics:
    """Metrics describing memory block relevance."""

    char_count: int
    linked_anchors_count: int
    session_iteration_density: float
    vertical_intersection_score: float


class JSONStructureAnalyzer:
    """Identify dynamic states for EvoMethod_SK memory blocks."""

    def __init__(self) -> None:
        self.gold_threshold = 0.7
        self.platinum_threshold = 0.9

    def calculate_metrics(self, block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> BlockMetrics:
        """Calculate metrics that drive block importance."""
        char_count = len(block.get("content", ""))
        linked_anchors = len(block.get("related_to", []))
        session_iteration_density = min(char_count / 1000, 1.0)
        vertical_score = self.calculate_vertical_intersection(block, all_blocks)

        return BlockMetrics(
            char_count=char_count,
            linked_anchors_count=linked_anchors,
            session_iteration_density=session_iteration_density,
            vertical_intersection_score=vertical_score,
        )

    def calculate_vertical_intersection(self, block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> float:
        """Compute vertical intersection score for a block."""
        related = block.get("related_to") or []
        if not related:
            return 0.0

        intersection_count = 0
        for related_block_id in related:
            related_block = next((candidate for candidate in all_blocks if candidate.get("block_id") == related_block_id), None)
            if related_block and related_block.get("related_to"):
                if block.get("block_id") in related_block.get("related_to", []):
                    intersection_count += 1

        return intersection_count / len(related)

    def determine_dynamic_state(self, metrics: BlockMetrics) -> str:
        """Return memory block dynamic state."""
        overall_score = (
            metrics.session_iteration_density * 0.4
            + metrics.vertical_intersection_score * 0.3
            + min(metrics.char_count / 500, 1.0) * 0.2
            + min(metrics.linked_anchors_count / 5, 1.0) * 0.1
        )

        if overall_score >= self.platinum_threshold:
            return "platinum"
        if overall_score >= self.gold_threshold:
            return "gold"
        return "normal"

    def analyze_session_memory(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze memory blocks and assign dynamic states."""
        blocks = session_data.get("color_blocks", [])

        for block in blocks:
            metrics = self.calculate_metrics(block, blocks)
            dynamic_state = self.determine_dynamic_state(metrics)

            block["dynamic_state"] = dynamic_state
            block["metrics"] = {
                "char_count_in_row": metrics.char_count,
                "linked_anchors_count": metrics.linked_anchors_count,
                "session_iteration_density": metrics.session_iteration_density,
                "vertical_intersection_score": metrics.vertical_intersection_score,
            }

            if dynamic_state == "platinum":
                block["shade_level"] = "very_dark"
            elif dynamic_state == "gold":
                block["shade_level"] = "dark"
            else:
                block.setdefault("shade_level", block.get("shade", "light"))

        return session_data

    def generate_quality_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate aggregate quality report for session memory."""
        blocks = session_data.get("color_blocks", [])

        gold_blocks = [block for block in blocks if block.get("dynamic_state") == "gold"]
        platinum_blocks = [block for block in blocks if block.get("dynamic_state") == "platinum"]
        block_count = len(blocks)

        return {
            "total_blocks": block_count,
            "gold_blocks": len(gold_blocks),
            "platinum_blocks": len(platinum_blocks),
            "memory_quality_score": (len(gold_blocks) * 0.7 + len(platinum_blocks) * 1.0) / block_count if block_count else 0.0,
            "recommendations": self.generate_recommendations(gold_blocks, platinum_blocks, blocks),
        }

    def generate_recommendations(
        self,
        gold_blocks: List[Dict[str, Any]],
        platinum_blocks: List[Dict[str, Any]],
        all_blocks: List[Dict[str, Any]],
    ) -> List[str]:
        """Produce recommendations for improving memory structure."""
        recommendations: List[str] = []

        if not platinum_blocks:
            recommendations.append(
                "Добавьте больше связей между ключевыми концепциями для создания платиновых блоков",
            )

        if len(all_blocks) < 5:
            recommendations.append("Сессия содержит мало блоков. Рекомендуется развить контекст.")

        return recommendations


def main() -> None:
    analyzer = JSONStructureAnalyzer()

    test_session = {
        "color_blocks": [
            {
                "block_id": "B001",
                "content": "Архитектура системы EvoMethod_SK основана на динамической памяти",
                "related_to": ["B002"],
                "shade": "dark",
            },
            {
                "block_id": "B002",
                "content": "Серверы устраняются через оптимизацию потоков данных",
                "related_to": ["B001"],
                "shade": "dark",
            },
        ]
    }

    analyzed = analyzer.analyze_session_memory(test_session)
    report = analyzer.generate_quality_report(analyzed)

    import json

    print("Анализ завершен:")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
