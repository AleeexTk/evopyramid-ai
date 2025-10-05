# EvoPyramid-AI Architecture Overview

This document captures the evolving architecture of the EvoPyramid-AI platform.
It will grow alongside the codebase and should be updated whenever the
architecture changes.

## Current State

- Repository scaffolding with community and automation guidelines.
- CI workflow running linting (ruff) and a Python bytecode compilation smoke test.
- Quantum context stack that combines intent, affect, and memory layers through
  asynchronous pipelines.

## Core Runtime Components

### Quantum Context Layer

- `apps/core/context/models.py` — shared dataclasses (`IntentResult`,
  `AffectResult`, `MemoryResult`) and the `MemoryLedgerProtocol`. The protocol
  makes it explicit how memory providers must behave and enables dependency
  injection when wiring higher level orchestrators.
- `apps/core/context/quantum_analyzer.py` — orchestrates the asynchronous
  gathering of intent, affect, and memory signals. The analyzer now accepts the
  shared protocol so test doubles or alternative ledgers can be supplied
  without modifying the analyzer internals.
- Pipelines (`agi_first_pipeline`, `soul_first_pipeline`, `role_first_pipeline`,
  `hybrid_pipeline`) transform the analyzed context into formatted responses
  that keep metadata attached for downstream consumers.

### Memory Pyramid Layer

- `apps/core/memory/pyramid_memory.py` — XML-backed hierarchical memory store.
  The `EnhancedDigitalSoulLedger` implements the shared protocol and returns a
  structured `MemoryResult`, ensuring the analyzer and integration engine work
  with the same snapshot of fragments.
- Memory fragments are stored as `MemoryFragment` dataclasses and weighted per
  layer (core, functional, emotional, meta). Relevance scoring is term-based and
  now feeds the `details` field that surfaces metadata alongside fragment IDs.

### Integration Layer

- `apps/core/integration/context_engine.py` — the EvoCodex context engine. It
  injects the shared ledger into the analyzer, processes pipelines based on the
  computed priority path, and exposes statistics about query distribution and
  timings.
- `tests/context/test_context_engine_memory_sync.py` verifies ledger snapshots
  remain synchronised after runtime mutations, guarding against regressions in
  the dependency injection wiring.

## Next Steps

- [ ] Describe deployment targets and runtime environments.
- [ ] Add architectural decision records under `docs/adr/`.
- [ ] Extend the architecture section with sequence diagrams covering the
      context-to-memory feedback loop.

## Contributing to the Architecture Doc

When you introduce a new subsystem or significant dependency, update this file
with a short summary and diagrams where applicable. Coordinate with the
collaboration practices outlined in `docs/EVO_COLLAB_GUIDE.md` so role sign-offs
and tooling bridges stay aligned with architectural changes. For LLM session
workflows, prime the context using `docs/EVO_SUMMON.md` to ensure the
architecture layer is "summoned" before gathering design feedback or running
ritual commands.
