# Quantum Context Engine Integration Guide

## Overview

The Quantum Context Engine extends EvoCodex with asynchronous context analysis, a hierarchical
memory model, and orchestration utilities. It is composed of:

- **QuantumContextAnalyzer** – multi-layer intent, affect, and memory analysis.
- **PyramidMemory** – XML-backed hierarchical memory with relevance scoring.
- **EvoCodexContextEngine** – integration layer combining analysis and memory lookups.

## Architecture

### QuantumContextAnalyzer

```python
analyzer = QuantumContextAnalyzer("запрос пользователя")
context = await analyzer.analyze()
```

Context layers include:

- `intent` – urgency, type, and confidence.
- `affect` – emotional resonance and intensity.
- `memory` – fragments, relevance, and linkage information.

Heuristics rely on deterministic keyword analysis rather than random sampling, so the
same query always produces the same contextual signature.

Priority paths are automatically determined:

- `AGI` – high-urgency technical focus.
- `SOUL` – emotionally resonant or philosophical queries.
- `ROLE` – memory-enriched contextualisation.
- `HYBRID` – balanced processing when no dominant signal is detected.

### PyramidMemory

- `core` – foundational knowledge (weight 1.0).
- `functional` – operational mechanics (weight 0.9).
- `emotional` – experiential knowledge (weight 0.8).
- `meta` – reflective system insights (weight 0.95).

Fragments are stored in `evo_memory.xml` by default. The system supports loading, saving, and
ranking fragments by relevance.

### EvoCodexContextEngine

```python
engine = EvoCodexContextEngine()
result = await engine.process_query("пример запроса")
```

The engine orchestrates analysis, augments context with pyramid memory, selects the appropriate
pipeline, and returns formatted responses along with statistics.

## Integration Steps

1. **Import the helpers**
   ```python
   from apps.core.integration.context_engine import enhanced_respond, get_context_engine
   ```
2. **Replace direct response generation**
   ```python
   response = await enhanced_respond(user_query, existing_context)
   ```
3. **Access the engine directly when extended control is required**
   ```python
   engine = get_context_engine()
   result = await engine.process_query(user_query)
   ```

### EvoMetaCore integration

`EvoMetaCore` automatically initialises the shared Quantum Context Engine (when
available) and exposes a synchronous helper for issuing queries:

```python
from apps.core.evo_core import EvoMetaCore

core = EvoMetaCore()
context_snapshot = core.process_context_query("Как работает контекстный анализ?")
```

To route a `process_task` call through the context engine, set the
`use_context_engine` flag or use the `context_query` task type:

```python
core.process_task({
    "type": "context_query",
    "data": "Подготовь обзор памяти Evo",
    "use_context_engine": True,
})
```

The Flask API now provides `/api/context_query` for direct HTTP access to the
context engine.

## Memory Management

Add new knowledge:

```python
await engine.add_to_memory({
    "name": "Новое знание",
    "content": "Содержание фрагмента памяти",
    "type": "core",
    "weight": 0.8,
    "emotional_tone": "curiosity",
})
```

## Testing

Run unit tests for the new modules:

```bash
python -m pytest tests/context/test_quantum_analyzer.py -v
python -m pytest tests/context/test_pyramid_memory.py -v
```

## Demonstration

```bash
python apps/core/integration/context_engine.py
```

## Next Steps

- Integrate with EvoNexusBridge for cross-system context sharing.
- Experiment with ML-backed relevance scoring.
- Visualise the PyramidMemory layers for auditing and tuning.
