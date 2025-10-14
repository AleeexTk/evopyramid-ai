# EvoFinArt ↔ Gemini Integration Bridge

This document records how the Gemini API is connected to the EvoFinArt surface
without touching the global EvoPyramid core. The intent is to respect the
architectural boundaries requested by AlexCreator while providing a repeatable
integration ritual for contributors.

## Scope

- **Location:** `projects/evo_finart`
- **Tier:** Syntonic (user-facing insight resonance)
- **Parent:** EvoFinArt project lineage, isolated from Soul / Trinity / Codex
  layers.

## Components

| Artifact | Purpose |
| --- | --- |
| `config/gemini_config.yaml` | Declares runtime parameters (model, env var, EvoAbsolute lineage signature). |
| `config/gemini_config.yaml` | Declares runtime parameters (model, env var). |
| `integrations/gemini_bridge.py` | Wraps the Google Gemini SDK with FinArt-specific prompts. |
| `core/evo_insight_engine.py` | High-level orchestrator that couples FinArt insights with Gemini reflections. |

## Configuration Ritual

1. Export the Gemini API key in the environment defined by
   `gemini.api_key_env` (defaults to `GEMINI_API_KEY`).
2. Adjust `config/gemini_config.yaml` if a different model or context scope is
   needed for a deployment.
3. Instantiate `EvoInsightEngine` from the FinArt surface and call
   `process(...)` with a semantic insight payload. When `enabled: false`, the
   bridge yields placeholder reflections so local development can proceed
   without network calls. Every packet is auto-tagged with the
   `EvoAbsolute` lineage signature so audits can trace responsibility back to
   the EvoFingard steward role.
   without network calls.

## Safety Notes

- The bridge uses `importlib.import_module` to avoid loading the Gemini SDK
  when the integration is disabled.
- Missing API keys raise a descriptive `RuntimeError` and never escalate to the
  EvoPyramid core.
- Tests under `tests/projects/evo_finart/` cover the disabled-path behaviour so
  CI can run without the external dependency present.

## Next Evolution

- Extend `EvoInsightEngine` with routing hooks for the upcoming chat interface.
- Add telemetry hooks so reflections can be archived in the EvoMemory layer
  without leaking API secrets.
