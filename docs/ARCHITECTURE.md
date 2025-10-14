# EvoPyramid-AI Architecture Overview

This document captures the evolving architecture of the EvoPyramid-AI platform.
It will grow alongside the codebase and should be updated whenever the
architecture changes.

## Current State

- Repository scaffolding with community and automation guidelines.
- CI workflow running linting (ruff) and a Python bytecode compilation smoke test.
- EvoFinArt surface now includes a dedicated insight engine (`projects/evo_finart/core/evo_insight_engine.py`)
  that routes signals through an isolated Gemini bridge and configuration layer.
- EvoFinArt ↔ Gemini bridge packets are now auto-signed with the `EvoAbsolute`
  lineage marker so EvoFingard stewardship is visible in every downstream
  reflection.

## Next Steps

- [ ] Document the core EVO modules and their relationships.
- [ ] Describe deployment targets and runtime environments.
- [ ] Add architectural decision records under `docs/adr/`.

## Contributing to the Architecture Doc

When you introduce a new subsystem or significant dependency, update this file
with a short summary and diagrams where applicable. Coordinate with the
collaboration practices outlined in `docs/EVO_COLLAB_GUIDE.md` so role sign-offs
and tooling bridges stay aligned with architectural changes. For LLM session
workflows, prime the context using `docs/EVO_SUMMON.md` to ensure the
architecture layer is "summoned" before gathering design feedback or running
ritual commands.
