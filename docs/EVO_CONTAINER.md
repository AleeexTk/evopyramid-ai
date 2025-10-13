# EVO Container Ω Manifest

The EVO Container orchestrates self-processing flows that convert external
signals into EvoPyramid chronicles. It is implemented as a set of modular
stages declared in `containers/evo_container/manifests/EVO_CONTAINER_MANIFEST.yaml`.

## Pipeline Stages

1. **Intake** – captures the external link and selected profile, recording the
   initial timestamp for the session.
2. **Analysis** – performs a lightweight keyword scan that classifies the link
   into semantic tags.
3. **Adapt** – translates semantic tags into adaptation intents that other
   systems can follow.
4. **Integrate** – wraps the adaptation plan into an integration contract aimed
   at EvoMemory.
5. **Sync** – enumerates telemetry channels (Archivarius, Trinity, Soul Sync)
   that will receive the contract.
6. **Harmonize** – compiles a single summary payload that is consumed by the
   EvoLink Narrator.
7. **Narrate** – handled by the EvoLink bridge, which writes a chronicle file in
   `containers/evo_container/evo_link_bridge/narrator/logs/chronicles/`.

## Profiles

Profiles define different container personae. Each profile lives under
`containers/evo_container/profiles/` and lists the preferred pipeline and
telemetry channel. The Ω manifest includes:

- `evochka.yaml` – empathetic observer tuned for resonance.
- `eva_absolute.yaml` – systems integrator focusing on governance.
- `eva_archivarius.yaml` – librarian persona maintaining memory lineage.
- `eva_architect.yaml` – structural designer aligning blueprints and simulation.

## Operating the Container

Use the `scripts/evo_manifest_runner.py` helper to run pipelines:

```bash
python scripts/evo_manifest_runner.py run-pipeline link_import_to_memory \
  --link "https://example.com/research" \
  --profile evochka
```

The script prints a JSON summary and writes chronicles plus telemetry updates to
support downstream modules.
