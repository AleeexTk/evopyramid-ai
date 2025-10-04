# EvoPyramid-AI

EvoPyramid-AI is an evolving research playground for experimenting with EVO
concepts, PEAR processors, and related ecosystem tooling. This repository now
includes the foundational community and automation scaffolding required to grow
safely.

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

## Documentation

- Architecture notes live in `docs/ARCHITECTURE.md`.
- Collaboration rituals and role expectations are documented in
  `docs/EVO_COLLAB_GUIDE.md`.
- Universal activation ritual for syncing any LLM with the architecture lives in
  `docs/EVO_SUMMON.md`.
- Additional ADRs will be located under `docs/adr/`.

## Community

For questions or proposals, open an issue or email maintainers@evopyramid.ai.
