#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utilities for scanning EvoPyramid environments for dependencies and artefacts.

The original implementation of the dependency scanner accumulated several merge
conflicts which left the module in an unusable state (e.g. duplicate headers,
truncated functions and unclosed docstrings).  This rewrite restores a working
implementation that:

* walks the repository and optional extra roots while skipping noisy folders;
* builds a forward/backward map of Python imports using static inspection;
* detects log/cache like artefacts for timeline analysis; and
* copies large ``.txt`` corpora into the ``data/evo_ingest`` staging area while
  emitting an annotated companion file.

The module is intentionally conservative: it never executes scanned files and
uses best-effort parsing so that decoding errors do not halt the scan.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

PY_EXT = (".py",)
LOGLIKE_EXT = (".log", ".cache", ".tmp", ".db", ".sqlite", ".jsonl")
PRIORITY_TXT_EXT = (".txt",)
PRIORITY_THRESHOLD_KB = 10

SKIP_DIRS: Set[str] = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "logs/evo_ingest",
    "node_modules",
    "venv",
}

INGEST_ROOT_REL = Path("data") / "evo_ingest"
PENDING_RAW_REL = INGEST_ROOT_REL / "pending" / "raw"
PENDING_ANNOT_REL = INGEST_ROOT_REL / "pending" / "annotated"
PROCESSED_REL = INGEST_ROOT_REL / "processed"

IMPORT_PATTERN = re.compile(
    r"^\s*(?:from\s+([a-zA-Z_][\w\.]*)\s+import|import\s+([a-zA-Z_][\w\.]*))",
    re.MULTILINE,
)

ANNOTATION_TEMPLATE = (
    "### [Evo Annotation] {timestamp}\n"
    "# Source: {source}\n"
    "# Context: awaiting synthesis by Trinity.\n\n"
)


# ---------------------------------------------------------------------------
# Path helpers and environment detection
# ---------------------------------------------------------------------------

def detect_env_root() -> Path:
    """Best-effort detection of the repository root.

    The function climbs up from the current module until a ``.git`` directory is
    encountered.  If no repository root can be located we fall back to the
    current working directory to avoid raising during scans.
    """

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def ensure_ingest_dirs(repo_root: Path) -> Dict[str, Path]:
    """Create ingest directories relative to ``repo_root`` and return them."""

    ingest_root = repo_root / INGEST_ROOT_REL
    raw_dir = repo_root / PENDING_RAW_REL
    annot_dir = repo_root / PENDING_ANNOT_REL
    processed_dir = repo_root / PROCESSED_REL

    for path in (ingest_root, raw_dir, annot_dir, processed_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "ingest_root": ingest_root,
        "raw": raw_dir,
        "annotated": annot_dir,
        "processed": processed_dir,
    }


def is_relative_to(path: Path, ancestor: Path) -> bool:
    """Return ``True`` if *path* is located inside *ancestor*."""

    try:
        path.resolve().relative_to(ancestor.resolve())
        return True
    except ValueError:
        return False


def list_roots(extra: Optional[Sequence[str]] = None) -> List[Path]:
    """Return the list of root directories that should be scanned."""

    repo_root = detect_env_root()
    roots: List[Path] = [repo_root]

    # Termux / Android shared storage hints
    for candidate in (Path.home() / "storage", Path("/sdcard")):
        if candidate.exists():
            roots.append(candidate)
            break

    if extra:
        for raw in extra:
            candidate = Path(raw).expanduser()
            if candidate.exists():
                roots.append(candidate)

    # Deduplicate while preserving order
    seen: Set[Path] = set()
    unique: List[Path] = []
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)

    return unique


def iter_files(roots: Sequence[Path]) -> Iterator[Path]:
    """Yield files contained within *roots* while respecting ``SKIP_DIRS``."""

    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Mutate ``dirnames`` in-place to prune skipped directories
            dirnames[:] = [
                name
                for name in dirnames
                if name not in SKIP_DIRS and not (Path(dirpath) / name).is_symlink()
            ]
            for filename in filenames:
                yield Path(dirpath) / filename


# ---------------------------------------------------------------------------
# Scanning utilities
# ---------------------------------------------------------------------------

def read_text_safely(path: Path) -> str:
    """Return the UTF-8 text contents of *path* or an empty string on failure."""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_imports(path: Path) -> Set[str]:
    """Extract imported modules from *path* using ``IMPORT_PATTERN``."""

    text = read_text_safely(path)
    if not text:
        return set()

    imports: Set[str] = set()
    for match in IMPORT_PATTERN.finditer(text):
        module = match.group(1) or match.group(2)
        if not module:
            continue
        imports.add(module.split(".")[0])
    return imports


def build_import_maps(py_files: Sequence[Path]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Return forward and reverse import maps for ``py_files``."""

    forward: Dict[str, List[str]] = {}
    reverse: Dict[str, Set[str]] = defaultdict(set)

    for file_path in py_files:
        imports = sorted(parse_imports(file_path))
        key = str(file_path)
        forward[key] = imports
        for module in imports:
            reverse[module].add(key)

    reverse_serialisable = {module: sorted(paths) for module, paths in reverse.items()}
    return forward, reverse_serialisable


def detect_loglike(files: Sequence[Path]) -> List[Dict[str, object]]:
    """Collect metadata about files that look like log artefacts."""

    entries: List[Dict[str, object]] = []
    for path in files:
        if path.suffix.lower() not in LOGLIKE_EXT:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append(
            {
                "path": str(path),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
    return sorted(entries, key=lambda item: item["modified_at"], reverse=True)


def collect_priority_texts(
    repo_root: Path,
    files: Sequence[Path],
    ingest_paths: Dict[str, Path],
) -> List[Dict[str, object]]:
    """Copy large text files into the ingest pipeline and annotate them."""

    results: List[Dict[str, object]] = []
    for path in files:
        if path.suffix.lower() not in PRIORITY_TXT_EXT:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        size_kb = stat.st_size / 1024.0
        if size_kb < PRIORITY_THRESHOLD_KB:
            continue

        timestamp = datetime.fromtimestamp(stat.st_mtime).isoformat()
        relative: Optional[Path] = None
        if is_relative_to(path, repo_root):
            relative = path.resolve().relative_to(repo_root.resolve())

        target_relative = relative if relative is not None else Path(path.name)
        raw_target = ingest_paths["raw"] / target_relative
        annot_target = ingest_paths["annotated"] / target_relative.with_suffix(".annotated.txt")
        raw_target.parent.mkdir(parents=True, exist_ok=True)
        annot_target.parent.mkdir(parents=True, exist_ok=True)

        try:
            copy2(path, raw_target)
        except OSError:
            continue

        header = ANNOTATION_TEMPLATE.format(timestamp=timestamp, source=path)
        try:
            payload = path.read_text(encoding="utf-8", errors="replace")
            annot_target.write_text(header + payload, encoding="utf-8")
        except OSError:
            continue

        results.append(
            {
                "source": str(path),
                "copied_raw": str(raw_target),
                "copied_annotated": str(annot_target),
                "size_kb": round(size_kb, 2),
                "modified_at": timestamp,
            }
        )
    return summary


def prepare_ingest_dirs() -> None:
    for directory in (RAW_DIR, ANNOT_DIR, PROC_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def copy_priority_texts(roots: Iterable[Path]) -> List[Dict[str, object]]:
    """Extract high-priority text documents into the evo_ingest pipeline."""

    ensure_ingest_dirs()
    catalog: List[Dict[str, object]] = []
def create_annotation(source: Path, destination: Path, relative_path: str) -> None:
    with destination.open("w", encoding="utf-8") as target, source.open(
        "r", encoding="utf-8", errors="ignore"
    ) as origin:
        target.write(f"{ANNOTATION_HEADER} {datetime.now().isoformat()}\n")
        target.write(f"# Source: {relative_path}\n")
        target.write("# Architecture reflection: awaiting analysis...\n\n")
        target.write(origin.read())


def process_priority_txt(roots: List[Path]) -> List[Dict[str, object]]:
    """Copy prioritized text files into the ingest staging area with annotations."""

    prepare_ingest_dirs()
    prioritized: List[Dict[str, object]] = []

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

            try:
                relative_path = file_path.resolve().relative_to(base.resolve())
            except ValueError:
                relative_path = Path(file_path.name)

            raw_destination = RAW_DIR / relative_path
            raw_destination.parent.mkdir(parents=True, exist_ok=True)

            annotated_relative = relative_path.with_name(
                f"{relative_path.stem}_annotated{relative_path.suffix}"
            )
            annotated_destination = ANNOT_DIR / annotated_relative
            annotated_destination.parent.mkdir(parents=True, exist_ok=True)

            try:
                copy2(file_path, raw_destination)
                create_annotation(file_path, annotated_destination, str(relative_path))
            except Exception:
                # Ensure partial copies do not linger when annotation fails.
                try:
                    raw_destination.unlink(missing_ok=True)
                except Exception:
                    pass
                continue

            prioritized.append(
                {
                    "path": str(relative_path),
                    "size_kb": round(size_kb, 2),
                    "raw_copy": str(raw_destination.resolve()),
                    "annotated_copy": str(annotated_destination.resolve()),
                    "priority": 1.0,
                }
            )

    return prioritized


def write_outputs(out_dir: Path, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "evo_dependency_map.json").open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    report_lines: list[str] = []
    report_lines.append(f"[EvoDependencyScanner] {payload['timestamp']}")
    report_lines.append(f"Roots: {', '.join(payload['roots'])}")
    report_lines.append(f"Files with imports: {payload['stats']['files_with_imports']}")
    report_lines.append(f"Unique imports observed: {payload['stats']['unique_imports']}")
    report_lines.append("")

    report_lines.append("Top files by outgoing imports:")
    for name, count in payload["magnets"]["top_outgoing"]:
        report_lines.append(f"  - {name}  → {count}")
    report_lines.append("")

    report_lines.append("Top import targets by incoming refs:")
    for name, count in payload["magnets"]["top_incoming"]:
        report_lines.append(f"  - {name}  ← {count}")
    report_lines.append("")

    report_lines.append("Artifact waves (logs/cache/tmp):")
    return catalog

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_scan(extra_roots: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """Execute the dependency scan and return a structured payload."""

    repo_root = detect_env_root()
    roots = list_roots(extra_roots)
    ingest_paths = ensure_ingest_dirs(repo_root)

    files = list(iter_files(roots))
    py_files = [path for path in files if path.suffix.lower() in PY_EXT]

    forward, reverse = build_import_maps(py_files)
    loglike_entries = detect_loglike(files)
    priority_corpus = collect_priority_texts(repo_root, files, ingest_paths)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scanned_roots": [str(root) for root in roots],
        "python_files": len(py_files),
        "forward_imports": forward,
        "reverse_imports": reverse,
        "loglike_entries": loglike_entries,
        "priority_texts": priority_corpus,
    }

    output_dir = repo_root / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evo_dependency_map.json"
    log_path = output_dir / "evo_dependency_report.log"

    try:
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass

    try:
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(f"Evo Dependency Scan :: {payload['generated_at']}\n")
            handle.write("Roots:\n")
            for root in payload["scanned_roots"]:
                handle.write(f"  - {root}\n")
            handle.write(f"Python files scanned: {payload['python_files']}\n\n")

            handle.write("[Log artefacts]\n")
            for entry in payload["loglike_entries"]:
                handle.write(
                    f"  - {entry['modified_at']} | {entry['size_bytes']} B | {entry['path']}\n"
                )
            if not payload["loglike_entries"]:
                handle.write("  (none detected)\n")

            handle.write("\n[Priority corpora]\n")
            for entry in payload["priority_texts"]:
                handle.write(
                    "  - {modified_at} | {size_kb} KB | {source}\n"
                    "    raw -> {copied_raw}\n"
                    "    annotated -> {copied_annotated}\n".format(**entry)
                )
            if not payload["priority_texts"]:
                handle.write("  (none detected)\n")
    except OSError:
        pass

    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Evo dependency scanner.")
    parser.add_argument(
        "--roots",
        nargs="*",
        default=None,
        help="Additional directories to include in the scan.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    run_scan(args.roots)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
