# EVO Container Ω

Evo Container Ω orchestrates the self-processing loop that guides how EvoPyramid
assimilates external knowledge. The container exposes modular stages—intake,
analysis, adaptation, integration, synchronisation, harmonisation—and binds them
to the EvoLink Narrator for chronicle generation.

## Module Topology

| Stage | Module | Purpose |
| --- | --- | --- |
| Signal Intake | `containers/evo_container/intake.py` | Capture raw payloads and persona context. |
| Analytical Weave | `containers/evo_container/analysis.py` | Derive hypotheses from the captured signal. |
| Adaptive Calibration | `containers/evo_container/adapt.py` | Translate insights into actionable directives. |
| Integrative Synthesis | `containers/evo_container/integrate.py` | Blend directives with memory channels. |
| Observer Sync | `containers/evo_container/syncer.py` | Align observers such as Trinity or Archivarius. |
| Harmonic Closure | `containers/evo_container/harmonize.py` | Produce a unified summary for downstream rituals. |
| Narrative Bridge | `containers/evo_container/evo_link_bridge/narrator/processor.py` | Convert timelines into Evo chronicles. |

## Manifest

The container is driven by `containers/evo_container/manifests/EVO_CONTAINER_MANIFEST.yaml`.
It lists available modules and the pipelines composing them. Phase 4 of the
roadmap activates the `evo_soul_sync` module, allowing the Soul Sync engine to
report the system's reflective state.

## Personas

Canonical persona profiles reside in `containers/evo_container/profiles/`:

- `evochka.yaml`
- `eva_absolute.yaml`
- `eva_archivarius.yaml`
- `eva_architect.yaml`

Each profile defines archetype, traits, and preferred integration protocols. The
runner can surface these traits when harmonising outputs.

## Running Pipelines

Use the universal runner:

```bash
python scripts/evo_manifest_runner.py run-pipeline link_import_to_memory --link "https://example" --profile evochka
```

The command emits a JSON snapshot of the execution context and writes a chronicle
under `logs/chronicles/`.

## Chronicle Output

Chronicles are stored as timestamped text files containing the formatted
timeline. These artefacts are consumed by Archivarius and Trinity observers to
trace how the container transformed the initial input into a harmonised state.
