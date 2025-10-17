"""Command-line client for interacting with EvoPyramid API modules."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

import requests

API_BASE = "http://127.0.0.1:8000"


def _pretty_print(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def codex_status() -> None:
    response = requests.get(f"{API_BASE}/codex/status", timeout=10)
    response.raise_for_status()
    data = response.json()
    print("🤖 Codex Status:")
    _pretty_print(data)


def codex_query(message: str, context: Dict[str, Any] | None = None) -> None:
    payload = {"message": message}
    if context:
        payload["context"] = context
    response = requests.post(f"{API_BASE}/codex/query", json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    print("🤖 Codex Response:")
    _pretty_print(data)


def module_i_status() -> None:
    response = requests.get(f"{API_BASE}/module_i/status", timeout=10)
    response.raise_for_status()
    data = response.json()
    print("🧠 Module I Status:")
    _pretty_print(data)


def module_i_analyze(question: str, context: Dict[str, Any] | None = None) -> None:
    payload: Dict[str, Any] = {"question": question}
    if context:
        payload["context"] = context
    response = requests.post(f"{API_BASE}/module_i/analyze", json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    print("🧠 Module I Analysis:")
    _pretty_print(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoPyramid API CLI")
    subparsers = parser.add_subparsers(dest="command")

    codex_parser = subparsers.add_parser("codex", help="Interact with the Codex module")
    codex_sub = codex_parser.add_subparsers(dest="codex_command")

    codex_sub.add_parser("status", help="Show Codex status")

    query_parser = codex_sub.add_parser("query", help="Send a query to Codex")
    query_parser.add_argument("message", help="Message to send to Codex")
    query_parser.add_argument("--context", help="Optional JSON context payload", default="{}")

    module_i_parser = subparsers.add_parser("module_i", help="Interact with Module I")
    module_i_sub = module_i_parser.add_subparsers(dest="module_i_command")
    module_i_sub.add_parser("status", help="Show Module I status")

    analyze_parser = module_i_sub.add_parser("analyze", help="Run Module I analysis")
    analyze_parser.add_argument("question", help="Question for Module I to analyze")
    analyze_parser.add_argument(
        "--context",
        help="Optional JSON context payload",
        default="{}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "codex":
            if args.codex_command == "status":
                codex_status()
                return 0
            if args.codex_command == "query":
                try:
                    context = json.loads(args.context)
                except json.JSONDecodeError as exc:
                    print(f"❌ Invalid JSON for context: {exc}")
                    return 1
                codex_query(args.message, context)
                return 0

        elif args.command == "module_i":
            if getattr(args, "module_i_command", None) == "status":
                module_i_status()
                return 0
            if getattr(args, "module_i_command", None) == "analyze":
                try:
                    context = json.loads(args.context)
                except json.JSONDecodeError as exc:
                    print(f"❌ Invalid JSON for context: {exc}")
                    return 1
                module_i_analyze(args.question, context)
                return 0
    except requests.ConnectionError:
        print(
            "❌ EvoPyramid API не запущен. Запусти: python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000",
        )
        return 1
    except requests.RequestException as exc:
        print(f"❌ API request failed: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
