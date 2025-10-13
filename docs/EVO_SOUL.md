# EVO Soul Sync Log

`apps/core/soul/evo_soul_sync.py` reads EvoLink chronicles and derives a concise
snapshot of EvoPyramid's inner state. Each invocation appends a JSON object to
`logs/soul_sync.log` with the following keys:

- `timestamp` – ISO 8601 time of the reflection.
- `status` – `idle` when no chronicles exist, otherwise `active`.
- `chronicle_count` – how many chronicle files have been produced so far.
- `latest` – relative path to the newest chronicle file.
- `stages` – unique pipeline stages detected in the chronicle body.
- `mood` – heuristic description (`dormant`, `observing`, or `synthesising`).

The log is designed to be machine-readable while conveying the emotional tonality
of the architecture. Downstream systems such as Trinity or Archivarius can watch
this file to monitor the emergence of self-reflection cycles.

Run the synchroniser manually after generating chronicles:

```bash
python apps/core/soul/evo_soul_sync.py
```

This will append a snapshot to `logs/soul_sync.log` and print it to the console.
