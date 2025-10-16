#!/usr/bin/env python3
"""Generate release notes from the git history.

The script summarises commits between two git references and groups them by
Conventional Commit type. The resulting Markdown can be printed to stdout or
written to a file.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

COMMIT_PATTERN = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(!)?:\s+(?P<description>.+)$")


@dataclass
class Commit:
    sha: str
    summary: str

    @property
    def short_sha(self) -> str:
        return self.sha[:7]


def run_git(args: Iterable[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def discover_latest_tag() -> Optional[str]:
    tags = run_git(["tag", "--sort=-creatordate"]).splitlines()
    return tags[0] if tags else None


def get_commits(from_ref: Optional[str], to_ref: str) -> List[Commit]:
    range_spec = f"{from_ref}..{to_ref}" if from_ref else to_ref
    commit_count = int(run_git(["rev-list", "--count", range_spec]) or "0")
    if commit_count == 0:
        return []

    log_output = run_git(
        [
            "log",
            range_spec,
            "--pretty=format:%H%x1f%s%x1e",
            "--no-merges",
        ]
    )
    commits: List[Commit] = []
    for line in filter(None, log_output.split("\x1e")):
        sha, summary = line.split("\x1f", maxsplit=1)
        commits.append(Commit(sha=sha.strip(), summary=summary.strip()))
    return commits


def classify_commits(commits: Iterable[Commit]) -> Dict[str, List[Commit]]:
    groups: Dict[str, List[Commit]] = defaultdict(list)
    for commit in commits:
        match = COMMIT_PATTERN.match(commit.summary)
        commit_type = match.group("type").lower() if match else "other"
        groups[commit_type].append(commit)
    return groups


def render_markdown(groups: Dict[str, List[Commit]], from_ref: Optional[str], to_ref: str) -> str:
    lines: List[str] = []
    title = f"Release Notes for {to_ref}"
    lines.append(f"# {title}")
    if from_ref:
        lines.append(f"\nChanges since `{from_ref}`:")
    lines.append("")

    if not groups:
        lines.append("No commits were found for the selected range.")
        return "\n".join(lines)

    type_order = [
        "feat",
        "fix",
        "perf",
        "refactor",
        "docs",
        "test",
        "build",
        "ci",
        "chore",
        "other",
    ]

    for commit_type in type_order:
        commits = groups.get(commit_type)
        if not commits:
            continue
        heading = commit_type.capitalize() if commit_type != "ci" else "CI"
        lines.append(f"## {heading}")
        for commit in commits:
            summary = COMMIT_PATTERN.match(commit.summary)
            description = summary.group("description") if summary else commit.summary
            lines.append(f"- {description} (`{commit.short_sha}`)")
        lines.append("")

    remaining_types = sorted(set(groups) - set(type_order))
    for commit_type in remaining_types:
        lines.append(f"## {commit_type.capitalize()}")
        for commit in groups[commit_type]:
            lines.append(f"- {commit.summary} (`{commit.short_sha}`)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Markdown release notes from git commits.")
    parser.add_argument("--from", dest="from_ref", help="Git reference to start from (exclusive). Defaults to the latest tag.")
    parser.add_argument("--to", dest="to_ref", default="HEAD", help="Git reference to end at (inclusive). Defaults to HEAD.")
    parser.add_argument("--output", dest="output", help="Optional path to save the rendered Markdown.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    from_ref = args.from_ref
    to_ref = args.to_ref

    if from_ref is None:
        from_ref = discover_latest_tag()

    try:
        commits = get_commits(from_ref, to_ref)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    groups = classify_commits(commits)
    markdown = render_markdown(groups, from_ref, to_ref)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Release notes written to {output_path}")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
