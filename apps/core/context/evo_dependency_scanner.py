"""EvoDependencyScanner — analyze code dependencies and high-priority text corpora.

This module performs a hybrid scan of the runtime environment to map Python import
relationships, discover log/cache artifacts, and extract high-value text sources
used for EvoPyramid cognition. It is designed to operate across desktop, cloud,
and Termux surfaces without mutating the original files.

Primary responsibilities:

* Traverse detected roots (repository + shared storage) while skipping noisy
  directories.
* Build a forward/backward map of Python imports for static dependency analysis.
* Detect log-like artifacts and correlate them into temporal "waves" of activity.
* Prioritize `.txt` documents larger than 10 KB, copying them into the
  `data/evo_ingest` pipeline with both raw and annotated variants for further
  assimilation by higher-level agents.
* Emit structured JSON (`logs/evo_dependency_map.json`) and a human-readable log
  (`logs/evo_dependency_report.log`) summarizing findings.

The scanner never executes target files; it relies on static inspection only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Dict, Iterable, List

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

PY_EXT = (".py",)
LOGLIKE_EXT = (".log", ".cache", ".tmp", ".db", ".sqlite", ".jsonl")
PRIORITY_TXT_EXT = (".txt",)
PRIORITY_THRESHOLD_KB = 10

# Directories to skip during traversal.
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    ".evo",
    ".cache",
}

# Regex pattern that captures both `from pkg import ...` and `import pkg` lines.
RE_IMPORT = re.compile(
    r"^(?:from\s+([a-zA-Z_][\w\.]*)\s+import\b|import\s+([a-zA-Z_][\w\.]*))",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Path helpers and environment detection
# ---------------------------------------------------------------------------

def detect_env_root() -> Path:
    """Best-effort detection of the repository root.

    If the module resides within the project tree the repo root is assumed to be
    three levels above the current file. Otherwise fallback to the user's home.
    """

    here = Path(__file__).resolve()
    if len(here.parents) >= 4:
        return here.parents[3]
    return Path.home()


def list_roots(extra: Iterable[str] | None = None) -> List[Path]:
    """Return the list of root directories to scan.

    The repository root is always included. On Android/Termux the shared storage
    mount is appended when accessible. Additional roots supplied through the
    CLI `--roots` flag are resolved when present.
    """

    roots: List[Path] = []
    repo_root = detect_env_root()
    roots.append(repo_root)

    # Termux shared storage hints.
    for candidate in (Path.home() / "storage", Path("/sdcard")):
        if candidate.exists():
            roots.append(candidate)
            break

    if extra:
        for raw in extra:
            path = Path(raw).expanduser()
            if path.exists():
                roots.append(path)

    # Deduplicate while preserving order.
    unique: List[Path] = []
    seen = set()
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def walk_files(base: Path) -> Iterable[Path]:
    """Yield files under *base* while pruning transient directories."""

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            yield Path(root) / name


def rel_to(root: Path, path: Path) -> str:
    """Return a path relative to *root* when possible."""

    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path.resolve())


def safe_read_text(path: Path) -> str:
    """Read text content using UTF-8 with fallbacks."""

    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# Dependency analysis
# ---------------------------------------------------------------------------

def is_code(path: Path) -> bool:
    return path.suffix.lower() in PY_EXT


def is_loglike(path: Path) -> bool:
    return path.suffix.lower() in LOGLIKE_EXT


def analyze_imports(py_text: str) -> List[str]:
    """Extract import targets from Python source text."""

    deps: List[str] = []
    for match in RE_IMPORT.finditer(py_text):
        pkg = match.group(1) or match.group(2)
        if pkg:
            deps.append(pkg.strip())
    return deps


def build_dependency_graph(roots: Iterable[Path]) -> Dict[str, Dict[str, List[str]]]:
    """Construct forward and reverse dependency structures.

    Returns a mapping with three keys:
        * graph: file -> list(imported module names)
        * reverse: module -> list(files importing it)
        * artifacts: log/cache metadata records
    """

    graph: Dict[str, set[str]] = defaultdict(set)
    reverse: Dict[str, set[str]] = defaultdict(set)
    artifacts: List[Dict[str, object]] = []

    for base in roots:
        for file_path in walk_files(base):
            if is_code(file_path):
                content = safe_read_text(file_path)
                imports = analyze_imports(content)
                if imports:
                    key = rel_to(base, file_path)
                    for dep in imports:
                        graph[key].add(dep)
                        reverse[dep].add(key)
            elif is_loglike(file_path):
                try:
                    artifacts.append(
                        {
                            "path": rel_to(base, file_path),
                            "kind": file_path.suffix.lower().lstrip("."),
                            "mtime": os.path.getmtime(file_path),
                        }
                    )
                except Exception:
                    continue

    return {
        "graph": {k: sorted(v) for k, v in graph.items()},
        "reverse": {k: sorted(v) for k, v in reverse.items()},
        "artifacts": artifacts,
    }


def rank_magnets(
    graph: Dict[str, List[str]], reverse: Dict[str, List[str]], limit: int = 20
) -> Dict[str, List[tuple[str, int]]]:
    """Identify the most connected nodes in the import graph."""

    top_outgoing = sorted(
        ((name, len(targets)) for name, targets in graph.items()),
        key=lambda pair: pair[1],
        reverse=True,
    )[:limit]

    top_incoming = sorted(
        ((name, len(sources)) for name, sources in reverse.items()),
        key=lambda pair: pair[1],
        reverse=True,
    )[:limit]

    return {"top_outgoing": top_outgoing, "top_incoming": top_incoming}


def correlate_artifacts(artifacts: List[Dict[str, object]], window_sec: int = 30) -> List[Dict[str, object]]:
    """Group artifact modifications that occur within *window_sec* seconds."""

    if not artifacts:
        return []

    ordered = sorted(artifacts, key=lambda item: item["mtime"])
    groups: List[List[Dict[str, object]]] = []
    current = [ordered[0]]

    for record in ordered[1:]:
        if record["mtime"] - current[-1]["mtime"] <= window_sec:
            current.append(record)
        else:
            groups.append(current)
            current = [record]
    groups.append(current)

    summary: List[Dict[str, object]] = []
    for cluster in groups:
        summary.append(
            {
                "start": cluster[0]["mtime"],
                "end": cluster[-1]["mtime"],
                "count": len(cluster),
                "kinds": sorted({item["kind"] for item in cluster}),
            }
        )

    return summary


# ---------------------------------------------------------------------------
# Priority text ingestion pipeline
# ---------------------------------------------------------------------------

INGEST_ROOT = Path("data") / "evo_ingest"
RAW_DIR = INGEST_ROOT / "pending" / "raw"
ANNOT_DIR = INGEST_ROOT / "pending" / "annotated"
PROC_DIR = INGEST_ROOT / "processed"


def ensure_ingest_dirs() -> None:
    for directory in (RAW_DIR, ANNOT_DIR, PROC_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def copy_priority_texts(roots: Iterable[Path]) -> List[Dict[str, object]]:
    """Extract high-priority text documents into the evo_ingest pipeline."""

    ensure_ingest_dirs()
    catalog: List[Dict[str, object]] = []

    for base in roots:
        for file_path in walk_files(base):
            if file_path.suffix.lower() not in PRIORITY_TXT_EXT:
                continue

            try:
                size_kb = os.path.getsize(file_path) / 1024
            except OSError:
                continue

            if size_kb < PRIORITY_THRESHOLD_KB:
                continue

            relative = rel_to(base, file_path)
            raw_target = RAW_DIR / file_path.name

            try:
                copy2(file_path, raw_target)
            except OSError:
                # Skip files that cannot be copied.
                continue

            annotated_target = ANNOT_DIR / f"{file_path.stem}_annotated.txt"
            try:
                original_text = safe_read_text(file_path)
                with annotated_target.open("w", encoding="utf-8") as annotated_file:
                    annotated_file.write(
                        "### [Evo Annotation] "
                        f"{datetime.now().isoformat()}\n"
                        f"# Source: {relative}\n"
                        "# Architecture reflection: pending synthesis by EvoCodex\n\n"
                    )
                    annotated_file.write(original_text)
            except OSError:
                # If annotation fails remove the raw copy to avoid inconsistencies.
                try:
                    raw_target.unlink(missing_ok=True)
                except Exception:
                    pass
                continue

            catalog.append(
                {
                    "path": str(file_path.resolve()),
                    "size_kb": round(size_kb, 2),
                    "raw_copy": str(raw_target.resolve()),
                    "annotated_copy": str(annotated_target.resolve()),
                    "priority": 1.0,
                }
            )

    return catalog


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def write_outputs(out_dir: Path, payload: Dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "evo_dependency_map.json").open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)

    lines: List[str] = []
    lines.append(f"[EvoDependencyScanner] {payload['timestamp']}")
    lines.append("Roots: " + ", ".join(payload["roots"]))
    lines.append(f"Files with imports: {payload['stats']['files_with_imports']}")
    lines.append(f"Unique imports observed: {payload['stats']['unique_imports']}")
    lines.append("")
    lines.append("Top files by outgoing imports:")
    for name, score in payload["magnets"]["top_outgoing"]:
        lines.append(f"  - {name}  → {score}")
    lines.append("")
    lines.append("Top import targets by incoming refs:")
    for name, score in payload["magnets"]["top_incoming"]:
        lines.append(f"  - {name}  ← {score}")
    lines.append("")
    lines.append("Artifact waves (logs/cache/tmp):")
    if payload["artifact_waves"]:
        for wave in payload["artifact_waves"]:
            start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wave["start"]))
            end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wave["end"]))
            kinds = ",".join(wave["kinds"])
            lines.append(f"  - [{start} … {end}]  count={wave['count']} kinds={kinds}")
    else:
        lines.append("  - (none detected)")

    lines.append("")
    lines.append("High-priority .txt documents (>10 KB):")
    if payload["priority_docs"]:
        for doc in payload["priority_docs"]:
            lines.append(
                "  • "
                f"{doc['path']}  → raw: {doc['raw_copy']} | annotated: {doc['annotated_copy']}"
                f" ({doc['size_kb']} KB)"
            )
    else:
        lines.append("  • (none identified)")

    with (out_dir / "evo_dependency_report.log").open("w", encoding="utf-8") as report_file:
        report_file.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("EvoDependencyScanner")
    parser.add_argument("--roots", nargs="*", help="Additional roots to scan")
    parser.add_argument("--out", default="logs", help="Output directory for reports")
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Artifact correlation window in seconds",
    )
    args = parser.parse_args(argv)

    roots = list_roots(args.roots)
    dependency_data = build_dependency_graph(roots)
    magnets = rank_magnets(dependency_data["graph"], dependency_data["reverse"])
    waves = correlate_artifacts(dependency_data["artifacts"], window_sec=args.window)
    priority_docs = copy_priority_texts(roots)

    payload: Dict[str, object] = {
        "timestamp": datetime.now().isoformat(),
        "roots": [str(root) for root in roots],
        "graph": dependency_data["graph"],
        "reverse": dependency_data["reverse"],
        "artifacts": dependency_data["artifacts"],
        "artifact_waves": waves,
        "magnets": magnets,
        "priority_docs": priority_docs,
        "stats": {
            "files_with_imports": len(dependency_data["graph"]),
            "unique_imports": len(dependency_data["reverse"]),
        },
    }

    output_dir = Path(args.out)
    write_outputs(output_dir, payload)

    print(
        json.dumps(
            {
                "status": "ok",
                "roots": payload["roots"],
                "files_with_imports": payload["stats"]["files_with_imports"],
                "unique_imports": payload["stats"]["unique_imports"],
                "priority_docs": len(priority_docs),
                "artifact_waves": len(waves),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI execution guard
    sys.exit(main())

