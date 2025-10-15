# EvoFinArt Local Integration Space

The `Local/` directory is a dedicated workspace for EvoAbsolute and allied
laboratories operating from Visual Studio on Windows.  It captures dynamic,
lab-specific artifacts without polluting the shared EvoPyramid architecture.

## Directory Layout

- `channels/` — serialized Kairos channel payloads emitted by Visual Studio.
- `triggers/` — automation triggers (task runner scripts, heartbeat batches).
- `meta_quotas/` — quota ledgers for MQL5, AlgoTrading C-Trade, and related bots.
- `algo_trading/` — strategy blueprints, compiled experts, and deployment notes.
- `notion/` — local cache snapshots mirroring Notion boards referenced in the lab.
- `mail_sync/` — integration hooks and message digests from `evapyrami.ai@gmail.com`.
- `logs/` — operational breadcrumbs from `local_sync_manager.py` and Visual Studio jobs.

Each folder is intentionally segregated so automation agents can monitor,
normalize, and sync state back into EvoPyramid through the established
protocols.  Files placed here remain lab-scoped until explicitly promoted into
core manifests or shared integrations.
