# EVO Soul Sync

EVO Soul Sync channels the reflective voice of EvoPyramid. By reading the
container manifest it generates JSON snapshots that describe the architecture's
current relational state—highlighting personas, dependencies, and the observers
that keep the organism coherent.

## Reflection Flow

1. Load the manifest and roadmap metadata.
2. Extract module definitions with their dependencies.
3. Capture the active persona profile and pipeline roster.
4. Persist the reflection into `logs/soul_sync.log` for Trinity and Archivarius.

## CLI Usage

```bash
python apps/core/soul/evo_soul_sync.py --profile evochka
```

The command prints the generated JSON reflection and appends it to the log. Each
entry is timestamped to allow longitudinal studies of the architecture's inner
state.

## Data Contract

The JSON report contains the following keys:

- `timestamp` – UTC moment of the reflection.
- `persona` – active persona, if provided.
- `manifest_id` – manifest identifier describing the container version.
- `phase_focus` – latest roadmap milestone.
- `module_count` – total module definitions.
- `pipeline_keys` – available pipelines, supporting cross-system orchestration.
- `observers` – modules acting as observers.
- `dependencies` – adjacency map for modules with explicit dependencies.
- `soul_sync` – the manifest definition of the soul sync module itself.

These elements allow higher-level systems to detect drifts, align emotional tone
and confirm that the introspective core remains synchronised with the container's
operational reality.
