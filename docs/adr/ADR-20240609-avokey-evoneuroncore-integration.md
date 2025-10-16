# ADR 2024-06-09: Evaluation of Avokey & EvoNeuronCore Prototype Integration

## Status
Accepted

## Context
Recent discovery of the `Avokey`, `EvoNeuron`, and `EvoNeuronCore` prototype raises the question of how (or if) these components should fold into EvoPyramid 2.0. The prototype introduces API key lifecycle handling, autonomous role-bound neurons, and a container generator aimed at deduplicating session narratives.

While the concepts align with the EvoPyramid triad (Soul, Trailblazer, Provocateur), the prototype is standalone, mixes runtime responsibilities, and lacks the guardrails mandated by the Evo CodeOps charter (security gating, observability, deterministic configuration management). We need a decision that preserves the architectural intent without compromising production standards.

## Decision
Integrate the prototype **as a research-oriented capability** behind EvoPyramid's Context Engine boundary rather than embedding it directly into production agents. We will:

1. Treat `Avokey` as an inspiration for a unified API credential format, formalised via the existing security matrix and implemented through the `Security Monitor` subsystem.
2. Fold the `EvoNeuron` concept into the Trailblazer experimentation sandbox, where stateful role experiments are run under controlled feature flags.
3. Use the `EvoContainerGenerator` heuristics to augment our knowledge-capture pipelines, but only after wrapping them in deterministic storage and deduplication services managed by the Memory Manager.
4. Document the boundaries, configuration contracts, and rollout plan as part of the EvoPyramid 2.0 integration roadmap.

## Consequences
- Provides a clear path to harvest valuable ideas (API key discipline, neuron evolution loops, container anchoring) without jeopardising stability.
- Keeps security, compliance, and observability enforcement inside existing EvoPyramid subsystems.
- Requires cross-team collaboration (Security, Knowledge Ops, Trailblazer) to define APIs and telemetry standards.
- Demands incremental delivery guarded by feature flags and ADR-backed iteration checkpoints.

## Implementation Steps
1. Draft interface specs for the unified API credential model and align with the Security Monitor team.
2. Define experiment scaffolding in Trailblazer to host neuron evolution loops with explicit lifecycle hooks.
3. Extend Memory Manager documentation to cover container deduplication and anchoring semantics.
4. Prepare migration notes and telemetry dashboards before any production rollout.

## References
- Avokey & EvoNeuronCore prototype shared on 2024-06-09 session.
- EvoPyramid 2.0 architecture overview (docs/ARCHITECTURE.md).
