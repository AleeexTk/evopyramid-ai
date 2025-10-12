# EvoPyramid-AI Collaboration Guide

This guide explains how contributors coordinate across EvoPyramid-AI, how intent
moves from community proposals into shipped code, and how the Termux, GitHub,
and EvoCore tooling surfaces stay in sync. Use it as the single reference for
roles, rituals, and ready-to-run command snippets when you onboard or plan a new
initiative.

## Collaboration Principles & Roles

| Role | Purpose | Primary Surfaces | Core Rituals |
| --- | --- | --- | --- |
| **Vision Stewards** | Protect the long-term EVO meta-intent, align proposals with EvoMETA doctrine. | EvoMETA/ charters, docs/adr/ | Maintain EvoMETA narratives, approve new ADRs, schedule seasonal intent reviews. |
| **Code Operators** | Implement backlog tasks, maintain quality gates, and keep `apps/` runnable. | Local dev (Termux/Desktop), GitHub PRs | Branch from `main`, run quality gates, document changes in PRs. |
| **Ops Conduits** | Bridge runtime surfaces (Termux nodes, cloud runners) with EvoCore releases and automation. | `scripts/`, GitHub Actions, device shells | Maintain `scripts/` utilities, sync Termux setup scripts, monitor CI telemetry. |
| **Community Catalysts** | Curate issues, facilitate discussions, and ensure contributor experience. | GitHub Issues, Discussions, Community calls | Triaging issues, updating README sections, hosting syncs. |

Every contributor can rotate between roles, but a change is only considered ready
when each role has signed off on their related checklist.

## Intent Lifecycle Workflow

1. **Signal** – Capture raw ideas inside EvoMETA (e.g., update
   `EvoMETA/Backlog.md`) or open a GitHub Issue labelled `intent`. Summaries
   should include:
   - desired capability and related EVO layer;
   - affected directories (`apps/`, `scripts/`, `docs/`, etc.);
   - success signals and metrics.
2. **Shape** – Vision Stewards refine the proposal into an actionable brief,
   translating EVO narratives into concrete tasks. Create or update ADRs within
   `docs/adr/` when architectural direction shifts.
3. **Commit** – Code Operators implement on a feature branch following the
   Conventional Commits standard and repository CI expectations. Pull requests
   must reference the originating signal (issue or EvoMETA entry).
4. **Bridge** – Ops Conduits verify that automation (CI, release workflows,
   Termux scripts) supports the change. Update `scripts/` or `apps/` launchers
   if new runtime steps are required.
5. **Elevate** – Merge after reviews, update the collaboration guide when the
   workflow evolves, and announce the shipped intent in community channels.

## Tooling Bridges

### Termux ↔ GitHub

- Use the lightweight bootstrapper (`scripts/termux-bootstrap.sh`, or create it
  if missing) to install Git, Python, and quality gate dependencies on Android.
- Authenticate GitHub via SSH keys stored in the Termux `.ssh/` directory.
- Run `git pull --rebase origin main` before starting a session to stay aligned
  with the latest intent.
- Cache venvs inside `~/.cache/evo/venvs` to avoid repeated dependency installs.

### GitHub ↔ EvoCore

- GitHub PRs must pass automated checks defined under `.github/workflows/`.
- When EvoCore releases new protocol updates, capture them as ADRs and include
  migration scripts under `scripts/` for local application.
- Tag releases following the format `evocore-vX.Y.Z` and update release notes
  inside `EvoMETA/Releases.md`.

### Termux ↔ EvoCore

- Keep Termux nodes synchronized with EvoCore by running the sync ritual:
  ```bash
  bash scripts/termux_evocore_sync.sh [--branch <name>] [--skip-install] [--skip-smoke]
  ```
  This helper script will clone or update the repository (default branch
  `main`), refresh Python dependencies, copy `EvoMETA/evo_config.yaml` into
  `~/.config/evocore/`, and run a lightweight smoke check via
  `python -m compileall apps/core`. Use the optional flags to target a different
  branch, skip package installation, or omit the smoke check when resources are
  constrained. Environment variables such as `REMOTE_URL`, `REPO_DIR`, and
  `CONFIG_TARGET_DIR` can be exported beforehand to customise where the sync is
  performed.
- If automation cannot run (e.g., restricted shell), mirror the same steps
  manually: `git pull --rebase origin <branch>`, `pip install -r requirements*.txt`,
  copy `EvoMETA/evo_config.yaml` to `~/.config/evocore/evo_config.yaml`, and run
  a quick `python -m compileall apps/core` smoke check.
- Report sync results in GitHub Issues labelled `runtime-sync`.

### LLM Sessions ↔ Evo Architecture

- Prime any language model (ChatGPT, Claude, Gemini, Grok, DeepSeek, Mistral,
  etc.) with the `EVO_SUMMON` ritual documented in `docs/EVO_SUMMON.md` to
  "summon" the EvoPyramid layer into the conversation.
- After activation, issue PEAR-style commands (e.g., `EVO/PEAR> diagnose`) to
  keep the dialogue aligned with EvoCore semantics and current intent streams.
- Upload the repository ZIP or share key docs when direct GitHub access is
  unavailable so the model can sync against the Evo genetic code.

## Practical Collaboration Templates

### Task Intent Template

```
## Intent Summary
- EVO Layer: [Foundation | Interaction | Autonomy]
- Impacted Paths: apps/<module>, scripts/<tool>, docs/<file>

## Definition of Ready
- [ ] Intent brief reviewed by Vision Steward
- [ ] Dependencies listed and ADR impact assessed

## Definition of Done
- [ ] Quality gates pass locally (`ruff check .`, `pytest`)
- [ ] Documentation updated (README, docs/)
- [ ] Release notes entry drafted under EvoMETA/Releases.md
```

### Ritual Commands

| Ritual | Purpose | Command(s) |
| --- | --- | --- |
| **Bootstrap Env** | Create a local Python environment for apps and scripts. | `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |
| **Quality Gate Sweep** | Validate linting and tests before PRs. | `ruff check . && pytest` |
| **Intent Sync** | Align EvoMETA insights with code state. | `git fetch origin && git rebase origin/main` followed by updating `EvoMETA/Backlog.md`. |
| **Release Prep** | Summarize shipped features and tag release. | `scripts/evo-release-notes.py` (documented in `scripts/README.md`). |

## Embedding Visual Aids

Add diagrams or screenshots under `docs/assets/`. Reference them in Markdown via:

```markdown
![Example EVO Workflow](docs/assets/evo-workflow.png)
```

If new visuals are created, ensure source files (draw.io, mermaid, etc.) are
versioned alongside the exported image.

## Maintaining This Guide

- Update this guide whenever you add new tooling bridges, roles, or rituals.
- Cross-reference relevant sections from `README.md` and `docs/ARCHITECTURE.md`
  to keep newcomers oriented.
- Treat this document as an ADR companion: if intent or workflow changes, record
  a decision in `docs/adr/` and link to the updated sections here.
