"""Internal utilities for EvoCodex governance integration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from collections.abc import Iterable
from typing import Any, Dict, List, Optional

import requests
import yaml


GITHUB_API_URL = "https://api.github.com"


def _list_rulesets(base_url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Return all existing rulesets for the repository."""

    rulesets: List[Dict[str, Any]] = []
    page = 1

    while True:
        response = requests.get(
            base_url,
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        if response.status_code >= 300:
            raise RuntimeError(
                "Failed to fetch existing rulesets: "
                f"{response.status_code} {response.text}"
            )

        payload = response.json()
        if isinstance(payload, dict) and "rulesets" in payload:
            batch: Iterable[Any] = payload.get("rulesets", [])
        else:
            batch = payload or []

        if not isinstance(batch, Iterable):
            raise RuntimeError(
                "Unexpected response structure when listing rulesets: "
                f"{payload}"
            )

        batch_list = [item for item in batch if isinstance(item, dict)]
        rulesets.extend(batch_list)

        if len(batch_list) < 100:
            break

        page += 1

    return rulesets


def _find_ruleset_id(rulesets: Iterable[Dict[str, Any]], name: str) -> Optional[int]:
    """Locate a ruleset's identifier by name."""

    for ruleset in rulesets:
        if not isinstance(ruleset, dict):
            continue
        if ruleset.get("name") == name and "id" in ruleset:
            identifier = ruleset["id"]
            if isinstance(identifier, int):
                return identifier
    return None


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

    existing_rulesets = _list_rulesets(base_url, headers)
    existing_id = _find_ruleset_id(existing_rulesets, ruleset_name)

    if existing_id:
        url = f"{base_url}/{existing_id}"
        response = requests.patch(url, headers=headers, json=data, timeout=30)
        if response.status_code == 404:
            # Ruleset was deleted after lookup. Attempt to create it afresh.
            response = requests.post(base_url, headers=headers, json=data, timeout=30)
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
