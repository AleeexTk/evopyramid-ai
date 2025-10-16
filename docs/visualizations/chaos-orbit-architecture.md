# Chaos-to-Orbit Architecture Sketch

This note captures the hand-drawn visualization shared for EvoPyramid-AI. The
sketch depicts how the platform coalesces "out of chaos" into concentric
structures with a navigable hierarchy of roles and systems.

## Reading the Diagram

The drawing uses spiraling orbits to represent emergent order. Moving from the
outer layers toward the center reveals how community, tooling, and the core
repository align.

1. **Outer Turbulence (Chaos Field)** – Dense graphite swirls show the raw idea
   space. Inputs, experiments, and community energy orbit freely here before
   being curated.
2. **Transition Orbit** – As paths stabilise, four nodes appear on an inner
   orbit. These nodes can be mapped to collaboration pillars (e.g. product,
   engineering, operations, governance) that regulate flow toward the core.
3. **PEARL Main Ring** – A square ring connects the four nodes with directed
   arrows. It models the PEARL coordination loop that routes knowledge and
   artifacts between collaborators while shielding the nucleus from noise.
4. **Core (Repo EVO 2.0)** – At the center the repository sits as the canonical
   source of truth. The annotations "EVO", "AI" and "PEARL" highlight that
   automation agents and human maintainers converge here.

## Design Principles Derived

- **Chaos is fuel** – Early-stage signals stay intentionally unfiltered. The
  system should allow rapid capture (issues, research logs) without imposing
  heavy process.
- **Concentric governance** – Each inner orbit adds structure. Converting ideas
  into backlog items, implementation tasks, and releases should follow the same
  inward spiral, with clear exit criteria at each boundary.
- **Bidirectional flow** – Arrows between nodes indicate feedback cycles. Tools
  like the EVO Summoning rituals and collaboration guides need to reflect this
  by encouraging frequent check-ins and synchronized agent contexts.
- **Protected core** – The repository must remain stable and auditable even as
  chaotic energy surrounds it. Automated tests, CI pipelines, and decision logs
  provide the "shield" effect depicted by the square ring.

## Next Iterations

- Recreate the sketch as a digital SVG layered diagram for easier updates.
- Map the four inner nodes to explicit EVO roles and document their inputs and
  outputs.
- Overlay existing automation (CI jobs, adapters, rituals) onto the orbits to
  test coverage and find gaps.
- Track these evolution steps in `docs/ARCHITECTURE.md` and reference ADRs when
  adding new structural rings.
