# Scripts Overview

This directory collects operational utilities that bootstrap environments and
support release hygiene for EvoPyramid-AI. Every script is designed to be
invoked from the repository root unless noted otherwise.

## `evo-release-notes.py`

Generate Markdown release notes from the git history.

```bash
scripts/evo-release-notes.py --from v0.4.0 --to HEAD --output docs/RELEASE_NOTES.md
```

- `--from` (optional): git reference that marks the starting point (exclusive).
  If omitted the script uses the latest tag.
- `--to`: git reference that marks the end of the range (inclusive). Defaults
  to `HEAD`.
- `--output` (optional): path to store the rendered Markdown. When omitted the
  content is printed to stdout.

The script groups commits by Conventional Commit type so that feature, bugfix,
refactor, and documentation changes are easy to scan during release prep.

## `setup_context_engine.sh`

Bash workflow that prepares the Quantum Context Engine locally:

1. Creates a Python virtual environment in `.venv` if missing.
2. Installs `requirements.txt` dependencies.
3. Verifies the presence of context-related packages under `apps/core/`.
4. Runs targeted pytest suites for the context engine.
5. Executes an integration demo via `apps.core.integration.context_engine`.

Run from the repository root:

```bash
bash scripts/setup_context_engine.sh
```

## `start_local.sh`

A PowerShell helper intended for Windows environments. It ensures a `venv`
virtual environment exists, installs dependencies from `requirements.txt` and
`requirements_context.txt`, then starts the Trinity Observer module.

```powershell
pwsh -File scripts/start_local.sh
```

## `start_termux.sh`

Bootstraps a Termux node on Android devices:

1. Installs baseline packages (`python`, `git`, `openssh`).
2. Clones the repository into `$HOME/evopyramid-ai` if needed.
3. Installs Python dependencies where available.
4. Launches `apps.core.trinity_observer` in the background and captures logs in
   `~/trinity.log`.

Invoke from a Termux shell:

```bash
bash scripts/start_termux.sh
```

## `termux_boot_autostart.sh`

Automates Termux boot synchronisation for EvoPyramid nodes that rely on the
Termux:Boot plugin. The script now delegates orchestration to the Python
runtime defined in `core/runtime/main.py`, ensuring that Termux is treated as a
first-class execution surface inside the architecture.

1. Stores the repository in `$HOME/evopyramid-ai` by default, aligning with
   Termux best practices to avoid `detected dubious ownership` errors on
   external storage. Override `EVO_PARENT_DIR` or `LOCAL_DIR` if you intentionally
   host the repo elsewhere.
2. Exports `EVO_RUNTIME_*` variables so the Python runtime can manage git
   synchronisation, wake locks, and module execution in a single, auditable
   flow.
3. Detects legacy clones under `/storage/emulated/0/EVO_LOCAL/…` or `/sdcard/…`
   and passes those paths to the runtime for automated migration into Termux's
   home directory.
4. Invokes `core/runtime/main.py --environment termux`, writing consolidated
   logs into `${EVO_PARENT_DIR}/logs/termux_boot/boot-<timestamp>.log` so Python
   and shell stages share the same timeline.
5. Leaves the launched module running in its own session so the Termux node can
   continue executing EvoPyramid rituals after the boot script exits.

Place the script under `~/.termux/boot/start-evopyramid.sh`, grant execute
permissions, and adjust environment variables (`EVO_PARENT_DIR`, `PY_ENV`, etc.)
to match the device topology.

> 🔁 **Migrating from external storage**: If you previously cloned the project
> under `/storage/emulated/0/…`, you can keep the old path in place. The runtime
> will migrate it into `$HOME/evopyramid-ai` automatically on the next boot.

📘 Подробная инструкция доступна в
[`docs/Termux_Runtime_Quickstart.md`](../docs/Termux_Runtime_Quickstart.md).

## `termux_evocore_sync.sh`

Manages manual synchronisation rituals between a Termux device and EvoCore. It
can be used when you need to trigger synchronisation outside of the boot
sequence or troubleshoot wake-lock behaviour.

```bash
bash scripts/termux_evocore_sync.sh
```

## `local_sync_manager.py`

Minimal placeholder script reserved for future EvoLocal synchronisation logic.
It currently emits a no-op message.

```bash
python scripts/local_sync_manager.py
```
