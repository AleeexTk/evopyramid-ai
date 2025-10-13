#!/usr/bin/env python3
"""Universal runner for Evo Container manifests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from containers.evo_container import cli  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return cli.cli(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
