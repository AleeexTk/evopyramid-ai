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
RE_IMPORT = re.compile(
    r"^(?:from\s+([a-zA-Z_][\w\.]*)\s+import\b|import\s+([a-zA-Z_][\w\.]*))",
    re.MULTILINE,
)
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
    roots: List[Path] = []
    repo_root = detect_env_root()
    roots.append(repo_root)
    for candidate in (Path.home() / "storage", Path("/sdcard")):
        if candidate.exists():
            roots.append(candidate)
            break
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


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


def walk_files(base: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            yield Path(root) / name


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
        pkg = match.group(1) or match.group(2)
        if pkg:
            deps.append(pkg.strip())
    return deps


def build_dependency_graph(roots: List[Path]) -> Dict[str, Dict]:
    graph: Dict[str, Set[str]] = defaultdict(set)
    reverse: Dict[str, Set[str]] = defaultdict(set)
    artifacts: List[Dict[str, object]] = []

    for base in roots:
        for file_path in walk_files(base):
            if is_code(file_path):
                content = safe_read_text(file_path)
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
        "graph": {node: sorted(values) for node, values in graph.items()},
        "reverse": {node: sorted(values) for node, values in reverse.items()},
        "artifacts": artifacts,
    }


def rank_magnets(graph: Dict[str, List[str]], reverse: Dict[str, List[str]]) -> Dict[str, List[tuple[str, int]]]:
    outgoing = sorted(((node, len(values)) for node, values in graph.items()), key=lambda x: x[1], reverse=True)
    incoming = sorted(((node, len(values)) for node, values in reverse.items()), key=lambda x: x[1], reverse=True)
    return {
        "top_outgoing": outgoing[:20],
        "top_incoming": incoming[:20],
    }


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
                "kinds": sorted({entry["kind"] for entry in group}),
            }
        )
    return summary


def prepare_ingest_dirs() -> None:
    for directory in (RAW_DIR, ANNOT_DIR, PROC_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def create_annotation(source: Path, destination: Path, relative_path: str) -> None:
    with destination.open("w", encoding="utf-8") as target, source.open(
        "r", encoding="utf-8", errors="ignore"
    ) as origin:
        target.write(f"{ANNOTATION_HEADER} {datetime.now().isoformat()}\n")
        target.write(f"# Source: {relative_path}\n")
        target.write("# Architecture reflection: awaiting analysis...\n\n")
        target.write(origin.read())


def process_priority_txt(roots: List[Path]) -> List[Dict[str, object]]:
    prepare_ingest_dirs()
    annotated: List[Dict[str, object]] = []

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
                "artifact_waves": len(artifact_waves),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
