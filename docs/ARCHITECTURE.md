# EvoPyramid-AI Architecture Overview

This document captures the evolving architecture of the EvoPyramid-AI platform.
It will grow alongside the codebase and should be updated whenever the
architecture changes.

## Current State

- Repository scaffolding with community and automation guidelines.
- CI workflow running linting (ruff) and a Python bytecode compilation smoke test.
- Chaos-to-Orbit sketch that models how the platform emerges from raw ideation
  into the protected EvoPyramid-AI core (see `docs/visualizations/chaos-orbit-architecture.md`).

## Next Steps

- [ ] Document the core EVO modules and their relationships.
- [ ] Describe deployment targets and runtime environments.
- [ ] Add architectural decision records under `docs/adr/`.
- [ ] Digitize the Chaos-to-Orbit visualization and link each orbit to concrete
      roles, tools, and rituals.

## Contributing to the Architecture Doc

When you introduce a new subsystem or significant dependency, update this file
with a short summary and diagrams where applicable. Coordinate with the
collaboration practices outlined in `docs/EVO_COLLAB_GUIDE.md` so role sign-offs
and tooling bridges stay aligned with architectural changes. For LLM session
workflows, prime the context using `docs/EVO_SUMMON.md` to ensure the
architecture layer is "summoned" before gathering design feedback or running
ritual commands.
