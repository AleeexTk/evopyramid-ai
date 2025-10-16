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

    if not isinstance(data, dict):
        raise ValueError("Ruleset file must define a mapping at the top level")

    ruleset_name = data.get("name")
    if not ruleset_name:
        raise ValueError("Ruleset definition must include a 'name' field")

    base_url = f"{GITHUB_API_URL}/repos/{repository}/rulesets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    lookup_response = requests.get(base_url, headers=headers, timeout=30)
    if lookup_response.status_code >= 300:
        raise RuntimeError(
            "Failed to fetch existing rulesets: "
            f"{lookup_response.status_code} {lookup_response.text}"
        )

    payload = lookup_response.json()
    if isinstance(payload, dict) and "rulesets" in payload:
        existing_rulesets = payload.get("rulesets", [])
    else:
        existing_rulesets = payload or []

    existing_id = None
    for ruleset in existing_rulesets:
        if isinstance(ruleset, dict) and ruleset.get("name") == ruleset_name:
            existing_id = ruleset.get("id")
            break

    if existing_id:
        url = f"{base_url}/{existing_id}"
        response = requests.patch(url, headers=headers, json=data, timeout=30)
    else:
        response = requests.post(base_url, headers=headers, json=data, timeout=30)

    if response.status_code >= 300:
        action = "update" if existing_id else "create"
        raise RuntimeError(
            f"Failed to {action} ruleset: "
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
