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
Termux:Boot plugin. The script ensures storage directories exist, keeps the
repository aligned with `origin/main`, replays local adjustments, and launches a
background runtime module while capturing logs on external storage.

1. Ensures `/storage/emulated/0/EVO_LOCAL/logs/termux_boot/` exists before
   logging to avoid the "No such file or directory" errors observed during
   manual dry runs.
2. Optionally clones the repository when `EVO_LOCAL/evopyramid-ai` is missing,
   preventing premature aborts on freshly provisioned devices.
3. Applies a stash-reset-pop cycle, creates commits for local tweaks, and uses
   `--force-with-lease` pushes to keep GitHub in sync without clobbering remote
   updates.
4. Launches `apps.core.trinity_observer` via the Termux Python interpreter by
   default; override `PYTHON_ENTRYPOINT` to start another module.

Place the script under `~/.termux/boot/start-evopyramid.sh`, grant execute
permissions, and adjust environment variables (`EVO_PARENT_DIR`, `PY_ENV`, etc.)
to match the device topology.
