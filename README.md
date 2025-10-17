# EvoPyramid-AI

EvoPyramid-AI is an evolving research playground for experimenting with EVO
concepts, PEAR processors, and related ecosystem tooling. This repository now
includes the foundational community and automation scaffolding required to grow
safely.

🔗 **EvoPyramid AI Repository:** [evopyramidai](https://github.com/AleeexTk/evopyramid-ai)

## Getting Started

1. Clone the repository and create a virtual environment:
   ```bash
   git clone <repo-url>
   cd evopyramid-ai
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install project dependencies once dependency files are published.
3. Run the default quality gates:
   ```bash
   ruff check .
   pytest
   ```

## Project Standards

- Conventional Commits for commit messages.
- Pull requests must pass the CI workflow defined in `.github/workflows/ci.yml`.
- Contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md) and review
  the [Contributing Guide](CONTRIBUTING.md).

## Configuration

Runtime configuration for the API layer is managed through environment
variables consumed by `apps.api.config.APISettings`. Key options include:

- `TRUSTED_HOSTS` – comma-separated list of domains passed to FastAPI's
  `TrustedHostMiddleware`. By default the service allows
  `localhost,127.0.0.1,evopyramid.com,api.evopyramid.com`. To extend the
  allow-list for staging or previews set, for example:

  ```bash
  export TRUSTED_HOSTS="localhost,127.0.0.1,staging.evopyramid.com"
  ```

All settings also support configuration through a `.env` file located in the
repository root.

## Documentation

- Architecture notes live in `docs/ARCHITECTURE.md`.
- Collaboration rituals and role expectations are documented in
  `docs/EVO_COLLAB_GUIDE.md`.
- The EvoCodex operating contract is published in
  `docs/EVO_CODEX_USER_CHARTER.md`.
- Universal activation ritual for syncing any LLM with the architecture lives in
  `docs/EVO_SUMMON.md`.
- Windows onboarding instructions for EvoFinArt are available in
  `docs/guides/EvoFinArt_Windows_Installation_RU.md` (Russian).
- Google Cloud deployment pathway for EvoPyramid-AI lives in
  `docs/guides/EvoPyramid_Google_Cloud_Deployment.md` (Russian), а исполняемые артефакты
  Cloud Deploy (рендер, apply и release) находятся в каталоге `clouddeploy/`, `scripts/render_clouddeploy.sh`
  и `skaffold.yaml`, которые автоматически исполняются из `cloudbuild.yaml`. Для ручного запуска
  полного Cloud Build цикла добавлен `scripts/trigger_cloud_build.sh`, прокидывающий необходимые
  substitutions и подтверждающий прохождение Cloud Deploy стейджей.
- The initial blueprint for the EvoFinArt chat interface prototype is tracked in
  `docs/blueprints/EvoFinArt_Chat_Interface_Prototype.md`.
- The Gemini bridge dedicated to EvoFinArt is documented in
  `docs/integration/EvoFinArt_Gemini_Bridge.md`.
- Additional ADRs will be located under `docs/adr/`.

## Community

For questions or proposals, open an issue or email maintainers@evopyramid.ai.

## Quick Run

- **Termux (Android):** `bash scripts/start_termux.sh`
- **Local workstation:** `bash scripts/start_local.sh`
