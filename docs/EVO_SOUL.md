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
