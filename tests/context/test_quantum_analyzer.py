"""Tests for the QuantumContextAnalyzer module."""

import asyncio

from apps.core.context.quantum_analyzer import QuantumContextAnalyzer, analyze_and_respond


class TestQuantumAnalyzer:
    """Test-suite covering the asynchronous analyzer behaviour."""

    def test_analyzer_initialization(self) -> None:
        analyzer = QuantumContextAnalyzer("тестовый запрос")
        assert analyzer.query == "тестовый запрос"
        assert analyzer.context_layers == {}
        assert analyzer.priority_path is None

    def test_analyzer_execution(self) -> None:
        analyzer = QuantumContextAnalyzer("срочный вопрос")
        context = asyncio.run(analyzer.analyze())
        assert isinstance(context, dict)
        assert set(context) == {"intent", "affect", "memory"}
        assert analyzer.priority_path in {"AGI", "SOUL", "ROLE", "HYBRID"}

    def test_priority_path_logic(self) -> None:
        queries = [
            "срочно помогите",
            "духовный смысл жизни",
            "ролевая модель поведения",
            "обычный вопрос",
        ]
        for query in queries:
            analyzer = QuantumContextAnalyzer(query)
            asyncio.run(analyzer.analyze())
            assert analyzer.priority_path in {"AGI", "SOUL", "ROLE", "HYBRID"}

    def test_full_pipeline(self) -> None:
        response = asyncio.run(analyze_and_respond("тестовый запрос"))
        assert isinstance(response, str)
        assert "QUANTUM CONTEXT RESPONSE" in response
