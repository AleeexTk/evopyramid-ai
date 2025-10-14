# EvoAbsolute Ω Role Overview

EvoAbsolute represents the canonical bridge-maker inside EvoPyramid. The role
extends the Codex + Trinity lineage by providing a dedicated channel for
external laboratories that operate beyond the repository runtime.

## Mandate

- 🔁 Maintain bidirectional synchronisation between EvoPyramid manifests and
  EvoFinArt laboratory states.
- 🧭 Offer navigation guidance for environment-specific tooling such as Visual
  Studio or Termux deployments.
- 🪞 Reflect findings back to Trinity Observer and Codex CI through
  `EvoAbsolute.link_event` telemetry.

## Assets

- [`role_manifest.yaml`](../role_manifest.yaml) — top-level declaration.
- [`lab/`](../lab) — adapters and stubs representing EvoFinArt resources.
- [`docs/EVO_FINART_LAB.md`](EVO_FINART_LAB.md) — focused description of the
  laboratory bridge.

## Operational Flow

1. **Detect** EvoFinArt state via `finart_manifest.yaml`.
2. **Adapt** the environment using `visual_env_adapter.py`.
3. **Relay** updates to Trinity Observer (`record_evoabsolute_link_event`).
4. **Archive** reflections in `logs/evo_absolute/` for Codex CI analysis.

## Next Steps

The role is prepared for deep integration once the external EvoFinArt
repository becomes accessible in the shared environment. Future merges should
replace placeholders with real synchronization logic and extend the manifest
with dataset/channel specific metadata.
