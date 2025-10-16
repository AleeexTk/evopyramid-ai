"""EvoBridge selective union synchronization orchestrator.

This module reads the :code:`EvoUnionFabric.yaml` manifest and produces a
selective synchronization manifest for the requested fractions and agents.
It keeps fraction purity intact by filtering the payload so that each agent
only exchanges the data types declared in the fabric manifest.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import yaml

FABRIC_PATH = Path(__file__).resolve().parent.parent / "EvoUnionFabric.yaml"


class EvoBridgeError(RuntimeError):
    """Raised when the fabric manifest is missing required fields."""


@dataclass(frozen=True)
class SyncRequest:
    """Represents a filtered synchronization intent."""

    fraction: str
    agents: Sequence[str]
    payload: str

    def to_dict(self) -> dict:
        return {
            "fraction": self.fraction,
            "agents": list(self.agents),
            "payload": self.payload,
        }


def load_fabric(path: Path = FABRIC_PATH) -> dict:
    """Load the EvoUnionFabric manifest and return its core dictionary."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "EvoUnionFabric" not in data:
        raise EvoBridgeError("EvoUnionFabric.yaml does not define EvoUnionFabric root")
    return data["EvoUnionFabric"]


def iter_sync_filters(fabric: dict) -> Iterable[SyncRequest]:
    """Yield :class:`SyncRequest` entries declared in the fabric manifest."""

    selective = fabric.get("selective_union_sync", {})
    filters = selective.get("filters", [])
    for item in filters:
        if not item:
            continue
        fraction = item.get("fraction")
        agents = item.get("agents", [])
        payload = item.get("payload")
        if not fraction or not agents or not payload:
            continue
        yield SyncRequest(fraction=fraction, agents=agents, payload=payload)


def filter_requests(
    requests: Iterable[SyncRequest],
    fractions: Optional[Sequence[str]] = None,
    agents: Optional[Sequence[str]] = None,
) -> List[SyncRequest]:
    """Filter sync requests by fractions and agents."""

    fraction_set = {fraction.lower() for fraction in fractions or []}
    agent_set = {agent.lower() for agent in agents or []}

    filtered: List[SyncRequest] = []
    for request in requests:
        fraction_match = not fraction_set or request.fraction.lower() in fraction_set
        agent_match = not agent_set or any(agent.lower() in agent_set for agent in request.agents)
        if fraction_match and agent_match:
            filtered.append(request)
    return filtered


def build_sync_manifest(
    fractions: Optional[Sequence[str]] = None,
    agents: Optional[Sequence[str]] = None,
    *,
    fabric: Optional[dict] = None,
) -> dict:
    """Build a structured synchronization manifest for the requested scope."""

    fabric = fabric or load_fabric()
    requests = list(iter_sync_filters(fabric))
    selected = filter_requests(requests, fractions=fractions, agents=agents)

    if not selected:
        raise EvoBridgeError("No matching selective_union_sync entries found")

    cross_sync = fabric.get("cross_sync", [])
    meta_bridge = fabric.get("meta_bridge", {})

    return {
        "meta": {
            "collapse_signal": meta_bridge.get("collapse_signal", "collective_collapse"),
            "audit_channel": meta_bridge.get("audit_channel", "EvoAuditBus"),
            "trigger": fabric.get("selective_union_sync", {}).get("trigger", "meta_bridge_request"),
        },
        "scope": {
            "fractions": fractions or "*",
            "agents": agents or "*",
        },
        "requests": [request.to_dict() for request in selected],
        "cross_sync": cross_sync,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a selective union sync manifest")
    parser.add_argument(
        "--fraction",
        dest="fractions",
        action="append",
        help="Limit synchronization to the specified fraction (can be used multiple times)",
    )
    parser.add_argument(
        "--agent",
        dest="agents",
        action="append",
        help="Limit synchronization to the specified agent (can be used multiple times)",
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_sync_manifest(fractions=args.fractions, agents=args.agents)
    except EvoBridgeError as error:
        parser.error(str(error))
        return 2

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
