# EvoFinArt Laboratory Bridge

The EvoFinArt lab is the inaugural project orchestrated by EvoAbsolute. It is a
Visual Studio centric environment that experiments with hybrid art/finance
signals and MT5 bridges.

## Embedded Artifacts

- `EvoBench.sln` — placeholder solution capturing Visual Studio topology.
- `signals_engine.py` — stub for the creative signal generator.
- `mt5_bridge.py` — shim documenting the MetaTrader 5 integration intent.
- `backtester.py` — deterministic backtester for CI friendly runs.
- `profiler.py` — collects runtime metrics for documentation and testing.
- `finart_manifest.yaml` — describes the external repository state.

## Adapter Workflow

`visual_env_adapter.py` acts as the orchestrator:

1. Loads `finart_manifest.yaml` to understand the lab surface.
2. Ensures EvoPyramid logging surfaces exist under `logs/evo_absolute/`.
3. Emits `EvoAbsolute.link_event` telemetry to Trinity Observer and Codex CI.
4. Writes reflective snapshots to `reflection.json` for future rituals.

## Usage

Run the adapter to inspect the lab:

```bash
python -m roles.evo_absolute.lab.visual_env_adapter status
```

Trigger a sync event:

```bash
python -m roles.evo_absolute.lab.visual_env_adapter sync
```

CI environments call `python -m roles.evo_absolute.lab.visual_env_adapter ci`
to register the bridge activity and verify manifests.
