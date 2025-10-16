"""Internal utilities for EvoCodex governance integration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import requests
import yaml


GITHUB_API_URL = "https://api.github.com"


def apply_ruleset(path: Path) -> None:
    """Apply a ruleset via the GitHub REST API."""
    if not path.exists():
        raise FileNotFoundError(f"Ruleset file not found: {path}")

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set in the environment")

    repository = os.getenv("GITHUB_REPOSITORY")
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is not set in the environment")

    with path.open("r", encoding="utf-8") as handle:
        data: Dict[str, Any] = yaml.safe_load(handle)

    url = f"{GITHUB_API_URL}/repos/{repository}/rulesets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code >= 300:
        raise RuntimeError(
            "Failed to apply ruleset: "
            f"{response.status_code} {response.text}"
        )

    print(json.dumps(response.json(), indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EvoCodex internal tooling")
    parser.add_argument(
        "--apply-ruleset",
        dest="ruleset",
        type=Path,
        help="Path to the ruleset YAML file to apply",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.ruleset:
        apply_ruleset(args.ruleset)
    else:
        raise SystemExit("No action specified")


if __name__ == "__main__":
    main()
