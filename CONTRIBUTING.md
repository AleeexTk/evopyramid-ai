# Contributing to EvoPyramid-AI

Thank you for your interest in contributing! This guide outlines how to engage
with the project and keep the repository healthy.

## Getting Started

1. Fork the repository and create a feature branch using the naming convention
   `feat/<topic>` or another appropriate prefix (e.g., `fix/`, `docs/`).
2. Create a Python virtual environment (`python -m venv .venv`) and activate it.
3. Install project dependencies. If a `requirements.txt` or other dependency
   definition file exists, install it before developing.
4. Run `ruff check .` and `pytest` locally before submitting a pull request.

## Development Workflow

- Use Conventional Commit messages (e.g., `feat(cli): add new command`).
- Keep commits focused and logically grouped.
- Update documentation when behavior or configuration changes.
- Add or update tests whenever you introduce new functionality.

## Pull Requests

- Fill out the pull request template completely, including risk assessment and
  rollback steps.
- Reference related issues with `Fixes #<issue-number>` or `Refs #<issue-number>`.
- Ensure the CI workflow passes before requesting a review.

## Code of Conduct

By participating in this project you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to
maintainers@evopyramid.ai.

## Questions?

Open a GitHub issue with the `question` label or reach out via
maintainers@evopyramid.ai.
