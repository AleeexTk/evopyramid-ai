"""Tests for the PyramidMemory module."""

from datetime import datetime
from pathlib import Path

from apps.core.memory.pyramid_memory import MemoryFragment, PyramidMemory


class TestPyramidMemory:
    """Test-suite for the hierarchical memory system."""

    def setup_method(self) -> None:
        self.tmp_file = Path("test_memory.xml")
        if self.tmp_file.exists():
            self.tmp_file.unlink()
        self.memory = PyramidMemory(str(self.tmp_file))

    def teardown_method(self) -> None:
        if self.tmp_file.exists():
            self.tmp_file.unlink()

    def test_memory_initialization(self) -> None:
        assert self.memory.fragments
        assert self.tmp_file.exists()

    def test_add_fragment(self) -> None:
        initial_count = len(self.memory.fragments)
        fragment = MemoryFragment(
            id="test_fragment",
            name="Тестовый фрагмент",
            content="Содержание тестового фрагмента",
            memory_type="core",
            weight=0.8,
            timestamp=datetime.now().isoformat(),
        )
        self.memory.add_fragment(fragment)
        assert len(self.memory.fragments) == initial_count + 1
        assert "test_fragment" in self.memory.fragments

    def test_find_relevant_fragments(self) -> None:
        fragment = MemoryFragment(
            id="specific_fragment",
            name="Уникальный тестовый концепт",
            content="Этот фрагмент содержит уникальные ключевые слова",
            memory_type="core",
            weight=0.9,
            timestamp=datetime.now().isoformat(),
        )
        self.memory.add_fragment(fragment)
        results = self.memory.find_relevant_fragments("уникальные ключевые слова", 0.5)
        assert results
        assert any(item.id == "specific_fragment" for item in results)

    def test_relevance_calculation(self) -> None:
        fragment = MemoryFragment(
            id="test_relevance",
            name="Тест релевантности",
            content="собака кошка птица",
            memory_type="core",
            weight=0.7,
            timestamp=datetime.now().isoformat(),
        )
        self.memory.add_fragment(fragment)
        results = self.memory.find_relevant_fragments("собака кошка", 0.5)
        assert results
        assert results[0].relevance_score >= 1 / 3
