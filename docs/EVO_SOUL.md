# Evo Soul Sync Guide

`soul_sync` translates raw chronicle artifacts into a high-level reflection that
Trinity Observer and Archivarius can consume. The goal is to surface the
emerging emotional signature of EvoPyramid without depending on brittle,
hard-coded heuristics.

## Chronicle Snapshots

Chronicles produced by the narrator begin with a JSON metadata header followed
by human-readable commentary. `evo_soul_sync` parses the header into
`ChronicleSnapshot` entries that capture:

- Absolute path to the chronicle
- Timestamp of creation
- Active profile
- Coherence score
- Readiness state determined during harmonization

## Reflection Payload

The soul sync process aggregates the most recent snapshots and produces a JSON
record containing:

- `generated_at`: UTC timestamp
- `total_chronicles`: count of available artifacts
- `average_coherence`: mean coherence score
- `readiness_ratio`: fraction of chronicles marked as ready
- `profiles_observed`: unique profile identifiers
- `recent`: up to five latest snapshots

Each invocation appends a new JSON line to `logs/soul_sync.log`, allowing other
systems to consume it as a structured event stream.

## Running the Sync

```bash
python apps/core/soul/evo_soul_sync.py
python apps/core/soul/evo_soul_sync.py --log-dir custom/chronicles --output /tmp/soul.log
```

The command prints the reflection to stdout in addition to writing it to the log
file. This mirrors the verification workflow described in the Omega blueprint.
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
