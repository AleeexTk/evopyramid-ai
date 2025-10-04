"""Integration layer combining the QuantumContextAnalyzer and PyramidMemory."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from apps.core.context.quantum_analyzer import (
    QuantumContextAnalyzer,
    agi_first_pipeline,
    hybrid_pipeline,
    role_first_pipeline,
    soul_first_pipeline,
)
from apps.core.memory.pyramid_memory import EnhancedDigitalSoulLedger, MemoryFragment, PyramidMemory


class EvoCodexContextEngine:
    """High-level orchestrator used to process EvoCodex queries."""

    def __init__(self, memory_system: PyramidMemory | None = None) -> None:
        self.quantum_analyzer = QuantumContextAnalyzer
        self.memory_system = memory_system or PyramidMemory()
        self.enhanced_ledger = EnhancedDigitalSoulLedger(memory=self.memory_system)
        self.stats = {
            "total_queries": 0,
            "path_distribution": {"AGI": 0, "SOUL": 0, "ROLE": 0, "HYBRID": 0},
            "avg_processing_time": 0.0,
        }

    async def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyse the query and build a contextual response."""

        del user_context  # Reserved for future integration hooks.
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        self.stats["total_queries"] += 1

        try:
            analyzer = self.quantum_analyzer(query)
            context = await analyzer.analyze()
            memory_context = await self.enhanced_ledger.find_related_fragments(query)
            context["memory"].update(memory_context)
            context["priority_path"] = analyzer.priority_path

            response = await self._execute_pipeline(analyzer.priority_path, context)
            self.stats["path_distribution"][analyzer.priority_path] += 1

            processing_time = loop.time() - start_time
            previous_total = self.stats["total_queries"] - 1
            self.stats["avg_processing_time"] = (
                self.stats["avg_processing_time"] * previous_total + processing_time
            ) / self.stats["total_queries"]

            return {
                "success": True,
                "response": response,
                "context": context,
                "processing_time": processing_time,
                "priority_path": analyzer.priority_path,
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            processing_time = loop.time() - start_time
            return {
                "success": False,
                "error": str(exc),
                "response": "Произошла ошибка при обработке контекста",
                "processing_time": processing_time,
            }

    async def _execute_pipeline(self, priority_path: str, context: Dict[str, Any]) -> str:
        pipelines = {
            "AGI": agi_first_pipeline,
            "SOUL": soul_first_pipeline,
            "ROLE": role_first_pipeline,
            "HYBRID": hybrid_pipeline,
        }
        pipeline = pipelines.get(priority_path, hybrid_pipeline)
        return await pipeline(context)

    def get_stats(self) -> Dict[str, Any]:
        """Return a copy of engine statistics."""

        return {
            "total_queries": self.stats["total_queries"],
            "path_distribution": self.stats["path_distribution"].copy(),
            "avg_processing_time": self.stats["avg_processing_time"],
        }

    async def add_to_memory(self, fragment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new fragment into the pyramid memory."""

        fragment = MemoryFragment(
            id=fragment_data.get("id", f"frag_{len(self.memory_system.fragments)}"),
            name=fragment_data["name"],
            content=fragment_data["content"],
            memory_type=fragment_data.get("type", "core"),
            weight=float(fragment_data.get("weight", 0.7)),
            timestamp=fragment_data.get("timestamp", ""),
            emotional_tone=fragment_data.get("emotional_tone"),
        )
        self.memory_system.add_fragment(fragment)
        self.enhanced_ledger.refresh_memory(force=True)
        return {"success": True, "fragment_id": fragment.id}


_context_engine: Optional[EvoCodexContextEngine] = None


def get_context_engine() -> EvoCodexContextEngine:
    """Return a singleton instance of the context engine."""

    global _context_engine
    if _context_engine is None:
        _context_engine = EvoCodexContextEngine()
    return _context_engine


async def enhanced_respond(query: str, existing_context: Optional[Dict[str, Any]] = None) -> str:
    """High-level helper returning a formatted contextual response."""

    engine = get_context_engine()
    result = await engine.process_query(query, existing_context)
    if result["success"]:
        return result["response"]
    return f"⚠️ Ошибка контекстного анализа: {result['error']}"


async def quick_analyze(query: str) -> Dict[str, Any]:
    """Run a quick analysis without generating the final response."""

    analyzer = QuantumContextAnalyzer(query)
    context = await analyzer.analyze()
    return {
        "priority_path": analyzer.priority_path,
        "urgency": context["intent"]["urgency"],
        "emotion": context["affect"]["emotion"],
        "has_memory_links": context["memory"]["has_strong_links"],
    }


async def demo_integration() -> None:
    """Demonstrate processing of several sample queries."""

    engine = get_context_engine()
    queries = [
        "Как работает Quantum Context Analyzer?",
        "Почему эта архитектура такая эффективная?",
        "Срочно нужно улучшить обработку ошибок",
        "Расскажи о духовных аспектах искусственного интеллекта",
    ]
    for query in queries:
        print(f"\n🎯 Запрос: {query}")
        result = await engine.process_query(query)
        if result["success"]:
            print(f"Путь: {result['priority_path']}")
            print(f"Время: {result['processing_time']:.2f}с")
            print(f"Ответ: {result['response'][:100]}...")
        else:
            print(f"Ошибка: {result['error']}")
    print(f"\n📊 Статистика: {engine.get_stats()}")


if __name__ == "__main__":
    asyncio.run(demo_integration())
