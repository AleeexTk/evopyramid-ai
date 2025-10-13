#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EvoDependencyScanner — статический анализ архитектуры и приоритетных текстов.

Этот модуль объединяет несколько когнитивных фаз EvoPyramid:
- Анализ импортов Python для построения карты зависимостей.
- Фиксацию логоподобных артефактов для выявления волн генерации.
- Приоритетное извлечение .txt-файлов (>10 КБ) в контур Evo Ingest.

Результаты сохраняются в JSON/лог отчёты и формируют контекст для Trinity,
Archivarius и SoulSync.
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
PY_EXT = (".py",)
LOGLIKE_EXT = (".log", ".cache", ".tmp", ".db", ".sqlite", ".jsonl")
PRIORITY_TXT_EXT = (".txt",)
PRIORITY_THRESHOLD_KB = 10

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
    roots: List[Path] = []
    repo_root = detect_env_root()
    roots.append(repo_root)

    # Termux shared storage
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
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


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


def is_code(path: Path) -> bool:
    return path.suffix.lower() in PY_EXT


def is_loglike(path: Path) -> bool:
    return path.suffix.lower() in LOGLIKE_EXT


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


def rank_magnets(graph: dict[str, list[str]], reverse: dict[str, list[str]]) -> dict:
    outgoing = sorted(((name, len(deps)) for name, deps in graph.items()), key=lambda x: x[1], reverse=True)
    incoming = sorted(((name, len(refs)) for name, refs in reverse.items()), key=lambda x: x[1], reverse=True)
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
            try:
                size_kb = os.path.getsize(file_path) / 1024
            except OSError:
                continue
            if size_kb < PRIORITY_THRESHOLD_KB:
                continue

            relative = rel_to(base, file_path)
            relative_path = Path(relative)

            raw_dest = ingest_dirs["pending_raw"] / relative_path
            raw_dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                copy2(file_path, raw_dest)
            except Exception:
                continue

            annotated_name = relative_path.stem + "_annotated" + relative_path.suffix
            annotated_path = relative_path.with_name(annotated_name)
            annot_dest = ingest_dirs["pending_annot"] / annotated_path
            annot_dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                annotate_copy(file_path, annot_dest, source_label=relative)
            except Exception:
                continue

            priority_docs.append(
                {
                    "original": str(file_path.resolve()),
                    "relative_to_root": relative,
                    "size_kb": round(size_kb, 2),
                    "raw_copy": str(raw_dest.resolve()),
                    "annotated_copy": str(annot_dest.resolve()),
                    "priority": 1.0,
                }
            )

    return priority_docs


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
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Окно (в секундах) для корреляции логоподобных артефактов",
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
        "timestamp": datetime.now().isoformat(),
        "roots": [str(root) for root in roots],
        "graph": dependency_data["graph"],
        "reverse": dependency_data["reverse"],
        "artifacts": dependency_data["artifacts"],
        "artifact_waves": artifact_waves,
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
