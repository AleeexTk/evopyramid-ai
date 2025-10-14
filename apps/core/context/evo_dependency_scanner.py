#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EvoDependencyScanner — статический анализ архитектуры и приоритетных текстов.

Этот модуль объединяет несколько когнитивных фаз EvoPyramid:
- Анализ импортов Python для построения карты зависимостей.
- Фиксацию логоподобных артефактов для выявления волн генерации.
- Приоритетное извлечение .txt-файлов (>10 КБ) в контур Evo Ingest.

Результаты сохраняются в JSON/лог отчёты и формируют контекст для Trinity,
Archivarius и SoulSync.
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
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EvoDependencyScanner — статический анализ зависимостей кода и побочных артефактов.
Фокус: Python-импорты + связка с логами/кэшами/временными файлами.
Среды: Termux / Desktop / Cloud (автоопределение корней).
Вывод: JSON-карта связей + человекочитаемый лог.
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
from typing import Iterable, List, Optional

# --- Константы и настройки ---
from typing import Dict, Iterable, List

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

PY_EXT = (".py",)
LOGLIKE_EXT = (".log", ".cache", ".tmp", ".db", ".sqlite", ".jsonl")
PRIORITY_TXT_EXT = (".txt",)
PRIORITY_THRESHOLD_KB = 10

# Directories to skip during traversal.
from typing import Dict, Iterable, List, Set

PY_EXT = (".py",)
LOGLIKE_EXT = (".log", ".cache", ".tmp", ".db", ".sqlite", ".jsonl")
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

INGEST_ROOT_REL = Path("data") / "evo_ingest"
PENDING_RAW_REL = INGEST_ROOT_REL / "pending" / "raw"
PENDING_ANNOT_REL = INGEST_ROOT_REL / "pending" / "annotated"
PROCESSED_REL = INGEST_ROOT_REL / "processed"

# Regex pattern that captures both `from pkg import ...` and `import pkg` lines.
RE_IMPORT = re.compile(
    r"^(?:from\s+([a-zA-Z_][\w\.]*)\s+import\b|import\s+([a-zA-Z_][\w\.]*))",
    re.MULTILINE,
)

ANNOTATION_HEADER = (
    "### [Evo Annotation] {timestamp}\n"
    "# Source: {source}\n"
    "# Architecture reflection: awaiting synthesis by Trinity.\n\n"
)


# --- Вспомогательные функции ---

def detect_env_root() -> Path:
    """Определяет корень репозитория относительно текущего файла."""
    here = Path(__file__).resolve()
    if len(here.parents) >= 4:
        return here.parents[3]
    return Path.cwd()


def is_relative_to(path: Path, ancestor: Path) -> bool:
    try:
        path.resolve().relative_to(ancestor.resolve())
        return True
    except ValueError:
        return False


def list_roots(extra: Optional[List[str]] = None) -> List[Path]:
    """Формирует список корней для сканирования."""

# ---------------------------------------------------------------------------
# Path helpers and environment detection
# ---------------------------------------------------------------------------

def detect_env_root() -> Path:
    """Best-effort detection of the repository root.

    If the module resides within the project tree the repo root is assumed to be
    three levels above the current file. Otherwise fallback to the user's home.
    """

    here = Path(__file__).resolve()
PRIORITY_TXT_EXT = (".txt",)
PRIORITY_THRESHOLD_KB = 10
INGEST_ROOT = Path("data/evo_ingest")
RAW_DIR = INGEST_ROOT / "pending" / "raw"
ANNOT_DIR = INGEST_ROOT / "pending" / "annotated"
PROC_DIR = INGEST_ROOT / "processed"
ANNOTATION_HEADER = "### [Evo Annotation]"


def detect_env_root() -> Path:
    """Определяем корневой репозитория: если скрипт внутри проекта — берем 3 уровня выше, иначе — HOME."""
    here = Path(__file__).resolve()
    if "evopyramid-ai" in here.parts:
        try:
            idx = here.parts.index("evopyramid-ai")
            return Path(*here.parts[: idx + 1])
        except ValueError:
            pass
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

    # Termux shared storage
    # Termux shared storage hints.
    roots: List[Path] = []
    repo_root = detect_env_root()
    roots.append(repo_root)
    for candidate in (Path.home() / "storage", Path("/sdcard")):
        if candidate.exists():
            roots.append(candidate)
            break

    if extra:
        for x in extra:
            p = Path(x)
            if p.exists():
                roots.append(p)

    # Убираем дубликаты
    unique: List[Path] = []
    seen = set()
    for r in roots:
        resolved = r.resolve()
        for raw in extra:
            path = Path(raw).expanduser()
            if path.exists():
                roots.append(path)

    # Deduplicate while preserving order.
    unique: List[Path] = []
    seen = set()
    if extra:
        for raw in extra:
            candidate = Path(raw)
            if candidate.exists():
                roots.append(candidate)
    unique: List[Path] = []
    seen: Set[Path] = set()
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

def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


def walk_files(base: Path, skip_paths: Iterable[Path] | None = None) -> Iterable[Path]:
    """Обходит файлы, исключая скрытые и служебные каталоги."""
    skip_resolved = [p.resolve() for p in (skip_paths or [])]
    base_resolved = base.resolve()

    for root, dirs, files in os.walk(base_resolved):
        root_path = Path(root).resolve()
        if any(is_relative_to(root_path, sp) for sp in skip_resolved):
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for name in files:
            file_path = root_path / name
            if any(is_relative_to(file_path, sp) for sp in skip_resolved):
                continue
            yield file_path
# ---------------------------------------------------------------------------
# Dependency analysis
# ---------------------------------------------------------------------------
def walk_files(base: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            yield Path(root) / name


def is_code(path: Path) -> bool:
    return path.suffix.lower() in PY_EXT


def is_loglike(path: Path) -> bool:
    return path.suffix.lower() in LOGLIKE_EXT


def analyze_imports(py_text: str) -> List[str]:
    """Extract import targets from Python source text."""

def rel_to(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path.resolve())


def analyze_imports(py_text: str) -> List[str]:
    deps: List[str] = []
    for match in RE_IMPORT.finditer(py_text):
        dep = match.group(1) or match.group(2)
        if dep:
            deps.append(dep.strip())
    return deps


def build_dependency_graph(roots: List[Path], skip_paths: Iterable[Path]) -> dict:
    graph: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    artifacts: list[dict] = []

    for base in roots:
        for file_path in walk_files(base, skip_paths=skip_paths):
            if is_code(file_path):
                content = safe_read_text(file_path)
                deps = analyze_imports(content)
                if deps:
                    key = rel_to(base, file_path)
                    for dep in deps:
                        graph[key].add(dep)
                        reverse[dep].add(key)
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
def build_dependency_graph(roots: List[Path]) -> Dict[str, Dict]:
    graph: Dict[str, Set[str]] = defaultdict(set)
    reverse: Dict[str, Set[str]] = defaultdict(set)
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
                dependencies = analyze_imports(content)
                if dependencies:
                    key = rel_to(base, file_path)
                    for dependency in dependencies:
                        graph[key].add(dependency)
                        reverse[dependency].add(key)
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
        "graph": {node: sorted(values) for node, values in graph.items()},
        "reverse": {node: sorted(values) for node, values in reverse.items()},
        "artifacts": artifacts,
    }


def rank_magnets(graph: dict[str, list[str]], reverse: dict[str, list[str]]) -> dict:
    outgoing = sorted(((name, len(deps)) for name, deps in graph.items()), key=lambda x: x[1], reverse=True)
    incoming = sorted(((name, len(refs)) for name, refs in reverse.items()), key=lambda x: x[1], reverse=True)
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
def rank_magnets(graph: Dict[str, List[str]], reverse: Dict[str, List[str]]) -> Dict[str, List[tuple[str, int]]]:
    outgoing = sorted(((node, len(values)) for node, values in graph.items()), key=lambda x: x[1], reverse=True)
    incoming = sorted(((node, len(values)) for node, values in reverse.items()), key=lambda x: x[1], reverse=True)
    return {
        "top_outgoing": outgoing[:20],
        "top_incoming": incoming[:20],
    }


def correlate_artifacts(artifacts: list[dict], window_sec: int = 30) -> list[dict]:
    if not artifacts:
        return []
    ordered = sorted(artifacts, key=lambda item: item["mtime"])
    groups: list[list[dict]] = []
    current: list[dict] = [ordered[0]]

    for entry in ordered[1:]:
        if entry["mtime"] - current[-1]["mtime"] <= window_sec:
            current.append(entry)
        else:
            groups.append(current)
            current = [entry]
    groups.append(current)

    waves: list[dict] = []
    for group in groups:
        waves.append(
def correlate_artifacts(artifacts: List[Dict[str, object]], window_sec: int = 30) -> List[Dict[str, object]]:
    if not artifacts:
        return []
    sorted_artifacts = sorted(artifacts, key=lambda entry: entry["mtime"])
    groups: List[List[Dict[str, object]]] = []
    current_group: List[Dict[str, object]] = [sorted_artifacts[0]]

    for artifact in sorted_artifacts[1:]:
        if artifact["mtime"] - current_group[-1]["mtime"] <= window_sec:
            current_group.append(artifact)
        else:
            groups.append(current_group)
            current_group = [artifact]
    groups.append(current_group)

    summary: List[Dict[str, object]] = []
    for group in groups:
        summary.append(
            {
                "start": group[0]["mtime"],
                "end": group[-1]["mtime"],
                "count": len(group),
                "kinds": sorted({item["kind"] for item in group}),
            }
        )
    return waves


def prepare_ingest_dirs(repo_root: Path) -> dict[str, Path]:
    mapping = {
        "root": (repo_root / INGEST_ROOT_REL).resolve(),
        "pending_raw": (repo_root / PENDING_RAW_REL).resolve(),
        "pending_annot": (repo_root / PENDING_ANNOT_REL).resolve(),
        "processed": (repo_root / PROCESSED_REL).resolve(),
    }
    for path in mapping.values():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
    return mapping


def annotate_copy(source_path: Path, destination: Path, source_label: str) -> None:
    with destination.open("w", encoding="utf-8") as target, source_path.open(
        "r", encoding="utf-8", errors="ignore"
    ) as original:
        header = ANNOTATION_HEADER.format(timestamp=datetime.now().isoformat(), source=source_label)
        target.write(header)
        target.write(original.read())


def process_priority_txt(
    roots: List[Path],
    repo_root: Path,
    skip_paths: Iterable[Path],
) -> list[dict]:
    ingest_dirs = prepare_ingest_dirs(repo_root)
    priority_docs: list[dict] = []

    for base in roots:
        for file_path in walk_files(base, skip_paths=skip_paths):
            if file_path.suffix.lower() not in PRIORITY_TXT_EXT:
                continue
            if is_relative_to(file_path, ingest_dirs["root"]):
                continue
                "kinds": sorted({entry["kind"] for entry in group}),
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
            report_lines.append(f"  - [{start} … {end}]  count={wave['count']} kinds={kinds}")
    else:
        report_lines.append("  - none detected in the selected window")
    report_lines.append("")

    report_lines.append("High-priority .txt documents (>10 KB):")
    if payload["priority_docs"]:
        for doc in payload["priority_docs"][:50]:
            report_lines.append(
                f"  • {doc['relative_to_root']}  → raw: {doc['raw_copy']}"
            )
    else:
        report_lines.append("  • none identified")

    with (out_dir / "evo_dependency_report.log").open("w", encoding="utf-8") as fp:
        fp.write("\n".join(report_lines))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser("EvoDependencyScanner")
    parser.add_argument("--roots", nargs="*", help="Дополнительные пути для сканирования")
    parser.add_argument("--out", default="logs", help="Каталог вывода отчётов")
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
        help="Окно (в секундах) для корреляции логоподобных артефактов",
        help="Artifact correlation window in seconds",
            if size_kb < PRIORITY_THRESHOLD_KB:
                continue
            relative_path = rel_to(base, file_path)
            dest_raw = RAW_DIR / file_path.name
            dest_annotated = ANNOT_DIR / f"{file_path.stem}_annotated.txt"
            try:
                copy2(file_path, dest_raw)
                create_annotation(file_path, dest_annotated, relative_path)
            except Exception:
                continue
            annotated.append(
                {
                    "path": relative_path,
                    "size_kb": round(size_kb, 2),
                    "raw_copy": str(dest_raw),
                    "annotated_copy": str(dest_annotated),
                    "priority": 1.0,
                }
            )
    return annotated


def write_outputs(out_dir: Path, payload: Dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "evo_dependency_map.json").open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)

    report_lines = [
        f"[EvoDependencyScanner] {payload['timestamp']}",
        f"Roots: {', '.join(payload['roots'])}",
        f"Files with imports: {payload['stats']['files_with_imports']}",
        f"Unique imports observed: {payload['stats']['unique_imports']}",
        "",
        "Top files by outgoing imports:",
    ]
    for name, value in payload["magnets"]["top_outgoing"]:
        report_lines.append(f"  - {name}  → {value}")
    report_lines.append("")
    report_lines.append("Top import targets by incoming refs:")
    for name, value in payload["magnets"]["top_incoming"]:
        report_lines.append(f"  - {name}  ← {value}")
    report_lines.append("")
    report_lines.append("Artifact waves (logs/cache/tmp):")
    for wave in payload["artifact_waves"]:
        start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wave["start"]))
        end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wave["end"]))
        report_lines.append(
            f"  - [{start} … {end}]  count={wave['count']} kinds={','.join(wave['kinds'])}"
        )
    report_lines.append("")
    report_lines.append("High-priority .txt documents (>10 KB):")
    for document in payload.get("priority_docs", [])[:50]:
        report_lines.append(
            "  • {path}  ({size} KB)  → raw={raw} annotated={annot}".format(
                path=document["path"],
                size=document["size_kb"],
                raw=document["raw_copy"],
                annot=document["annotated_copy"],
            )
        )
    with (out_dir / "evo_dependency_report.log").open("w", encoding="utf-8") as report_file:
        report_file.write("\n".join(report_lines))


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser("EvoDependencyScanner")
    parser.add_argument("--roots", nargs="*", help="Дополнительные корни для сканирования")
    parser.add_argument("--out", default="logs", help="Каталог для вывода логов/JSON")
    parser.add_argument(
        "--window", type=int, default=30, help="Окно корреляции артефактов (секунды)"
    )
    args = parser.parse_args(argv)

    roots = list_roots(args.roots)
    repo_root = detect_env_root().resolve()
    ingest_root = (repo_root / INGEST_ROOT_REL).resolve()
    skip_paths = [ingest_root]

    dependency_data = build_dependency_graph(roots, skip_paths=skip_paths)
    magnets = rank_magnets(dependency_data["graph"], dependency_data["reverse"])
    artifact_waves = correlate_artifacts(dependency_data["artifacts"], window_sec=args.window)
    priority_docs = process_priority_txt(roots, repo_root, skip_paths=skip_paths)

    payload = {
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
        "artifact_waves": artifact_waves,
        "artifact_waves": waves,
        "magnets": magnets,
        "priority_docs": priority_docs,
        "stats": {
            "files_with_imports": len(dependency_data["graph"]),
            "unique_imports": len(dependency_data["reverse"]),
        },
    }

    out_dir = Path(args.out)
    write_outputs(out_dir, payload)

    summary = {
        "status": "ok",
        "roots": payload["roots"],
        "files_with_imports": payload["stats"]["files_with_imports"],
        "unique_imports": payload["stats"]["unique_imports"],
        "artifact_waves": len(payload["artifact_waves"]),
        "priority_docs": len(payload["priority_docs"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
    data = build_dependency_graph(roots)
    magnets = rank_magnets(data["graph"], data["reverse"])
    artifact_waves = correlate_artifacts(data["artifacts"], window_sec=args.window)
    priority_docs = process_priority_txt(roots)

    payload = {
        "timestamp": datetime.now().isoformat(),
        "roots": [str(root) for root in roots],
        "graph": data["graph"],
        "reverse": data["reverse"],
        "artifacts": data["artifacts"],
        "artifact_waves": artifact_waves,
        "magnets": magnets,
        "stats": {
            "files_with_imports": len(data["graph"]),
            "unique_imports": len(data["reverse"]),
        },
        "priority_docs": priority_docs,
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
                "artifact_waves": len(artifact_waves),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI execution guard
    sys.exit(main())


if __name__ == "__main__":
    main(sys.argv[1:])
