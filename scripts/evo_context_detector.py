"""EvoContext Split Protocol (ECSP) environment detector.

This utility inspects the current execution surface and emits a structured
summary so EvoCodex and allied agents can adapt behavior (Termux runtime,
Desktop development, or Cloud automation).
"""
from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

MATRIX_PATH = Path(__file__).resolve().parent.parent / "EVO_CONTEXT_MATRIX.yaml"


@dataclasses.dataclass
class DetectionRule:
    """Detection thresholds for a surface."""

    env_flags: Iterable[str]
    path_contains: Iterable[str]
    platform_any_of: Iterable[str]


@dataclasses.dataclass
class SurfaceProfile:
    """Runtime description for an ECSP surface."""

    surface_id: str
    tier: str
    description: str
    logging_category: str
    logging_sink: str
    rule: DetectionRule


def _load_yaml_matrix(path: Path) -> Optional[Dict[str, Dict[str, object]]]:
    """Load the context matrix if PyYAML is present."""

    spec = importlib.util.find_spec("yaml")
    if spec is None:
        return None

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        return None

    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    with path.open("r", encoding="utf-8") as handle:
        return module.safe_load(handle)  # type: ignore[attr-defined]


def _fallback_surfaces() -> Dict[str, SurfaceProfile]:
    """Return embedded ECSP surface definitions."""

    return {
        "termux": SurfaceProfile(
            surface_id="termux",
            tier="runtime-mobile",
            description=(
                "Termux / Android node optimized for lightweight monitoring "
                "and rapid local checks."
            ),
            logging_category="runtime-mobile",
            logging_sink="logs/runtime-mobile/context.log",
            rule=DetectionRule(
                env_flags=(),
                path_contains=("com.termux",),
                platform_any_of=("Linux",),
            ),
        ),
        "desktop": SurfaceProfile(
            surface_id="desktop",
            tier="dev-workstation",
            description=(
                "Primary architectural editing surface (VS Code, GitHub Desktop, JetBrains)."
            ),
            logging_category="dev-desktop",
            logging_sink="logs/dev-desktop/context.log",
            rule=DetectionRule(
                env_flags=("VSCODE_GIT_IPC_HANDLE",),
                path_contains=(),
                platform_any_of=("Windows", "Darwin", "Linux"),
            ),
        ),
        "cloud": SurfaceProfile(
            surface_id="cloud",
            tier="ci-cd",
            description="Automated pipelines (GitHub Actions, Render, Railway).",
            logging_category="sync-cloud",
            logging_sink="logs/sync-cloud/context.log",
            rule=DetectionRule(
                env_flags=("GITHUB_ACTIONS", "CI"),
                path_contains=(),
                platform_any_of=("Linux",),
            ),
        ),
    }


def _extract_surfaces(matrix: Optional[Dict[str, object]]) -> Dict[str, SurfaceProfile]:
    """Translate YAML dictionary into SurfaceProfile mapping."""

    if matrix is None:
        return _fallback_surfaces()

    surfaces_section = matrix.get("surfaces", {}) if isinstance(matrix, dict) else {}
    profiles: Dict[str, SurfaceProfile] = {}
    for surface_id, payload in surfaces_section.items():
        if not isinstance(payload, dict):
            continue

        detection = payload.get("detection", {})
        rule = DetectionRule(
            env_flags=tuple(detection.get("env_flags", []) or []),
            path_contains=tuple(detection.get("path_contains", []) or []),
            platform_any_of=tuple(detection.get("platform_any_of", []) or []),
        )

        logging = payload.get("logging", {})
        profiles[surface_id] = SurfaceProfile(
            surface_id=surface_id,
            tier=str(payload.get("tier", "unknown")),
            description=str(payload.get("description", "")),
            logging_category=str(logging.get("category", "")),
            logging_sink=str(logging.get("sink", "")),
            rule=rule,
        )
    return profiles or _fallback_surfaces()


def detect_surface(
    profiles: Dict[str, SurfaceProfile],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    system: Optional[str] = None,
) -> Dict[str, object]:
    """Return detection result with matched indicators and confidence."""

    cwd = cwd or Path.cwd()
    env = env or dict(os.environ)
    system = system or platform.system()

    matches: List[Dict[str, object]] = []
    cwd_str = str(cwd)

    for surface_id, profile in profiles.items():
        matched_flags = [flag for flag in profile.rule.env_flags if flag in env]
        matched_paths = [marker for marker in profile.rule.path_contains if marker in cwd_str]
        matched_system = system in profile.rule.platform_any_of if profile.rule.platform_any_of else False

        score = len(matched_flags) * 3 + len(matched_paths) * 3
        if matched_system:
            score += 1

        matches.append(
            {
                "surface": surface_id,
                "score": score,
                "matched_flags": matched_flags,
                "matched_paths": matched_paths,
                "platform_match": matched_system,
            }
        )

    best = max(matches, key=lambda item: item["score"], default={})
    surface = best.get("surface") if best else "unknown"
    fallback_used = False

    if best and best.get("score", 0) <= 1:
        # No strong signals were found; choose fallback ordering.
        fallback_order = ("desktop", "termux", "cloud")
        for candidate in fallback_order:
            if candidate in profiles:
                surface = candidate
                fallback_used = candidate != best.get("surface")
                break

    if fallback_used:
        best = next((item for item in matches if item["surface"] == surface), {})

    profile = profiles.get(surface) if surface else None
    confidence = min(best.get("score", 0) / 3.0, 1.0) if best else 0.0

    result = {
        "surface": surface or "unknown",
        "tier": profile.tier if profile else "unknown",
        "description": profile.description if profile else "",
        "confidence": round(confidence, 3),
        "matched_indicators": best if best else {},
        "logging": {
            "category": profile.logging_category if profile else "",
            "sink": profile.logging_sink if profile else "",
        },
        "detected_at": {
            "cwd": cwd_str,
            "platform": system,
        },
    }

    return result


def emit(result: Dict[str, object], as_json: bool) -> None:
    """Print detection result in JSON or table form."""

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print("EvoContext Surface:", result["surface"])
    print("Tier:", result.get("tier", "unknown"))
    print("Confidence:", result.get("confidence", 0.0))
    print("Description:", result.get("description", ""))
    matched = result.get("matched_indicators", {})
    if matched:
        print("Matched Flags:", ", ".join(matched.get("matched_flags", [])) or "—")
        print("Matched Paths:", ", ".join(matched.get("matched_paths", [])) or "—")
        print("Platform Match:", matched.get("platform_match", False))
    print("Log Category:", result.get("logging", {}).get("category", ""))
    print("Log Sink:", result.get("logging", {}).get("sink", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect EvoContext execution surface.")
    parser.add_argument("--json", action="store_true", help="Emit detection result as JSON.")
    parser.add_argument(
        "--export",
        type=Path,
        help="Optional path to write JSON detection summary for downstream tooling.",
    )
    args = parser.parse_args()

    matrix = _load_yaml_matrix(MATRIX_PATH)
    profiles = _extract_surfaces(matrix)
    result = detect_surface(profiles)

    if args.export:
        args.export.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    emit(result, as_json=args.json)


if __name__ == "__main__":
    main()
