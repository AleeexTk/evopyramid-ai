# Termux Runtime Integration

The EvoRuntime orchestrator embedded under `core/runtime/` promotes Termux
nodes to first-class citizens of the EvoPyramid architecture. It bridges shell
automation with Python orchestration so Termux:Boot devices can synchronise,
heal, and execute the same rituals as desktop or cloud peers.

## Design Principles

- **Environment abstraction** – `RuntimeAdapter` defines the lifecycle needed to
  prepare a working tree, enforce Git safety, and launch EvoPyramid modules. The
  base class handles repository migrations, hard resets, stash cycles, and
  guarded pushes with `--force-with-lease`.
- **Termux specialisation** – `TermuxAdapter` extends the base behaviour with
  wake-lock management, legacy path migration (e.g. `/storage/emulated/0`), and
  interpreter fallbacks tuned for Android.
- **Declarative configuration** – The `RuntimeConfig` dataclass reads
  `EVO_RUNTIME_*` environment variables or an optional YAML/JSON manifest,
  enabling per-device overrides without modifying source code.
- **Orchestrated entrypoint** – `core/runtime/main.py` detects the active
  environment, selects the correct adapter, and records a unified log stream for
  diagnostics. When asked to operate in Termux it automatically queues migration
  paths, safe-directory registration, and the Trinity Observer module by
  default.

## Boot Flow

1. `scripts/termux_boot_autostart.sh` seeds environment variables and invokes
   `core/runtime/main.py --environment termux`.
2. The runtime resolves configuration, ensures legacy clones are migrated into
   `$HOME/evopyramid-ai`, and registers Git safe directories as needed.
3. Repository synchronisation runs through a stash/reset/pop pipeline before
   committing and pushing local adjustments with `--force-with-lease` if pending
   changes remain.
4. The requested module (default `apps.core.trinity_observer`) launches in a new
   session so it continues running after the boot wrapper exits.

## Extending to New Environments

The adapter pattern allows additional execution surfaces—desktop nodes,
containerised agents, or CI runners—to plug in by subclassing
`RuntimeAdapter`. Each adapter can:

- Override wake-lock semantics or process launch behaviour.
- Inject environment-specific migrations or permission fixes.
- Provide different defaults for repository locations and logging policies.

When adding a new adapter:

1. Implement a subclass under `core/runtime/`.
2. Export it from `core/runtime/__init__.py`.
3. Update `core/runtime/main.py` to route the relevant `--environment` value to
   the new adapter.
4. Document the workflow under `docs/` and register the lineage in
   `EVO_ARCH_MAP.yaml`.

## Configuration Reference

| Variable | Purpose |
| --- | --- |
| `EVO_RUNTIME_REPO_DIR` | Absolute path to the working tree the runtime should manage. |
| `EVO_RUNTIME_REPO_URL` | Git URL used when cloning the repository. |
| `EVO_RUNTIME_LOGS_DIR` | Directory where runtime log files will be created. |
| `EVO_RUNTIME_ENTRY_POINT` | Python module (for `python -m`) launched after synchronisation. |
| `EVO_RUNTIME_ENTRY_ARGS` | Additional arguments appended after the entry module. |
| `EVO_RUNTIME_PYTHON_BIN` | Path to the Python interpreter that should execute the module. |
| `EVO_RUNTIME_GIT_REMOTE` | Remote name used for fetch/reset/push operations. |
| `EVO_RUNTIME_GIT_BRANCH` | Branch name aligned during synchronisation. |
| `EVO_RUNTIME_AUTO_SAFE_DIRECTORY` | Set to `false` to skip registering Git safe directories. |
| `EVO_RUNTIME_PUSH_CHANGES` | Set to `false` to skip committing/pushing local changes. |
| `EVO_RUNTIME_MIGRATE_SOURCES` | Colon-separated list of legacy directories to migrate. |
| `EVO_RUNTIME_CONFIG` | Path to a YAML/JSON file providing the same keys as environment variables. |

## Troubleshooting

- **Runtime exits immediately** – Inspect the shared boot log under
  `${EVO_PARENT_DIR}/logs/termux_boot/` for Python tracebacks. Failures are
  surfaced through the exit code of `core/runtime/main.py`.
- **Wake lock fails** – Termux may block wake-lock acquisition until the user
  grants battery optimisation exemptions. The runtime logs the failure but
  continues so manual sessions can still proceed.
- **Repository not migrated** – Ensure the legacy path is readable by Termux and
  not already linked into the target directory. The runtime skips migration when
  the destination exists to avoid clobbering active clones.

By consolidating Termux orchestration into Python we reduce shell divergence,
embed Git safety into the architecture, and unlock future adapters that can
reuse the same lifecycle contracts.
