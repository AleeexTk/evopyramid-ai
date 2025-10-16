"""Automated export of Kairos ↔ Logos dashboards for EvoDashboard.

This utility reads the Trinity telemetry ledger (``logs/trinity_metrics.log``)
and synthesises JSON payloads for the Kairos Compass, Cohesion Dashboard, and
Timeline ↔ Map bundle.  The generated files are stored inside the EvoDashboard
workspace so GitHub Actions and local rituals can surface the latest
visualisations without manual exports from Notion.

The exporter is intentionally tolerant of partially populated log entries.
Historical records have evolved alongside the architecture; some carry the
``KairosEvent`` schema while others reflect ``TrinityObserver`` snapshots.  To
keep the dashboards available across eras, the exporter performs progressive
field extraction with sensible defaults and documents any skipped anomalies in
its output metadata.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence


DEFAULT_LOG_PATH = Path("logs/trinity_metrics.log")
DEFAULT_OUTPUT_DIR = Path("EvoDashboard")


@dataclass
class DashboardArtifacts:
    """Container for the generated dashboard payloads."""

    kairos_compass: Dict[str, Any]
    cohesion_dashboard: Dict[str, Any]
    timeline_map: Dict[str, Any]


def _load_log_records(log_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL records from the Trinity metrics log.

    Parameters
    ----------
    log_path:
        Path to ``logs/trinity_metrics.log``.

    Returns
    -------
    list[dict]
        Parsed records.  Invalid JSON lines are skipped.
    """

    if not log_path.exists():
        return []

    records: List[Dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)):
        for item in value:
            parsed = _parse_float(item)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, dict):
        for key in ("value", "amount", "score", "metric", "avg", "mean", "val"):
            if key in value:
                parsed = _parse_float(value[key])
                if parsed is not None:
                    return parsed
        for item in value.values():
            parsed = _parse_float(item)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        mapping = {"low": 0.25, "medium": 0.5, "high": 0.85}
        if lowered in mapping:
            return mapping[lowered]

        cleaned = value.strip().replace("°", "")
        cleaned = cleaned.replace("−", "-")
        cleaned = cleaned.replace("—", "-")
        cleaned = cleaned.replace("%", "")
        cleaned = cleaned.replace("_", "")
        cleaned = re.sub(r"[A-Za-z]+$", "", cleaned)
        cleaned = cleaned.replace(" ", "")

        if "," in cleaned and "." not in cleaned:
            sign = ""
            core = cleaned
            if core and core[0] in "+-":
                sign = core[0]
                core = core[1:]
            parts = core.split(",")
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                if len(parts[-1]) <= 2:
                    cleaned = sign + parts[0] + "." + "".join(parts[1:])
                else:
                    cleaned = sign + "".join(parts)
            else:
                cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            match = re.search(r"[-+]?\d+(?:[.,]\d+)?", cleaned)
            if match:
                candidate = match.group(0)
                if "," in candidate and "." not in candidate:
                    candidate = candidate.replace(",", ".")
                else:
                    candidate = candidate.replace(",", "")
                try:
                    return float(candidate)
                except ValueError:
                    return None
            return None
    return None


def _parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(round(value))
    if isinstance(value, (list, tuple)):
        for item in value:
            parsed = _parse_int(item)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, dict):
        for key in ("value", "count", "level", "metric"):
            if key in value:
                parsed = _parse_int(value[key])
                if parsed is not None:
                    return parsed
        for item in value.values():
            parsed = _parse_int(item)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            float_candidate = _parse_float(stripped)
            if float_candidate is not None:
                return int(round(float_candidate))
            return None
    return None


def _extract_first(record: Dict[str, Any], *paths: Iterable[str]) -> Any:
    def _traverse(node: Any, path: Sequence[str]) -> Any:
        if not path:
            return node

        key = path[0]
        rest = path[1:]

        if isinstance(node, dict):
            if key not in node:
                return None
            return _traverse(node[key], rest)

        if isinstance(node, (list, tuple)):
            for item in node:
                result = _traverse(item, path)
                if result is not None:
                    return result
            return None

        return None

    for path in paths:
        result = _traverse(record, tuple(path))
        if result is not None:
            return result
    return None


def _extract_timestamp(record: Dict[str, Any]) -> str:
    candidate = _extract_first(
        record,
        ("timestamp",),
        ("observed_at",),
        ("time",),
        ("meta", "timestamp"),
        ("system_state", "last_peak_moment"),
        ("components", "chronos", "timestamp"),
    )
    if isinstance(candidate, str):
        return candidate
    return datetime.now(timezone.utc).isoformat()


def _extract_agent_tags(record: Dict[str, Any]) -> List[str]:
    raw_tags = _extract_first(
        record,
        ("agent_tags",),
        ("agents",),
        ("meta", "agent_tags"),
        ("metadata", "agent_tags"),
    )
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    if isinstance(raw_tags, (list, tuple)):
        flattened: List[str] = []
        for tag in raw_tags:
            if isinstance(tag, (list, tuple)):
                flattened.extend(str(inner).strip() for inner in tag if str(inner).strip())
            else:
                tag_str = str(tag).strip()
                if tag_str:
                    flattened.append(tag_str)
        return flattened
    return [str(raw_tags)]


def _build_kairos_compass(records: List[Dict[str, Any]], source: Path) -> Dict[str, Any]:
    matrix: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: {"low": {"count": 0, "avg_impact": 0.0}, "mid": {"count": 0, "avg_impact": 0.0}, "high": {"count": 0, "avg_impact": 0.0}}
    )
    events: List[Dict[str, Any]] = []
    skipped = 0

    for record in records:
        impact = _parse_float(
            _extract_first(
                record,
                ("impact",),
                ("metrics", "impact"),
                ("components", "kairos", "impact"),
                ("state_vectors", "conceptual_clarity"),
                ("trinity_coherence",),
            )
        )
        kairos_level = _parse_int(
            _extract_first(
                record,
                ("kairos_level",),
                ("metrics", "kairos_level"),
                ("components", "kairos", "level"),
                ("components", "kairos", "kairos_level"),
            )
        )

        if impact is None or kairos_level is None:
            skipped += 1
            continue

        if impact < 0:
            impact = 0.0
        if impact > 1:
            # Normalise wide ranges by assuming 0-100 semantics.
            impact = min(impact / 100.0, 1.0)

        bucket = "low"
        if impact >= 0.66:
            bucket = "high"
        elif impact >= 0.33:
            bucket = "mid"

        bucket_entry = matrix[str(kairos_level)][bucket]
        new_count = bucket_entry["count"] + 1
        bucket_entry["avg_impact"] = (
            (bucket_entry["avg_impact"] * bucket_entry["count"] + impact) / new_count
        )
        bucket_entry["count"] = new_count

        events.append(
            {
                "timestamp": _extract_timestamp(record),
                "kairos_level": kairos_level,
                "impact": round(impact, 4),
                "agent_tags": _extract_agent_tags(record),
                "lineage": _extract_first(record, ("lineage",), ("metadata", "lineage")),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_log": str(source),
        "records": len(events),
        "skipped_records": skipped,
        "matrix": matrix,
        "events": events,
    }


def _build_cohesion_dashboard(records: List[Dict[str, Any]], source: Path) -> Dict[str, Any]:
    latency_values: List[float] = []
    replay_values: List[int] = []
    love_values: List[float] = []
    coherence_values: List[float] = []

    for record in records:
        latency = _parse_float(
            _extract_first(
                record,
                ("latency_ms",),
                ("metrics", "latency_ms"),
                ("observability", "latency_ms"),
            )
        )
        if latency is not None:
            latency_values.append(latency)

        retries = _parse_int(
            _extract_first(
                record,
                ("retries",),
                ("metrics", "retries"),
                ("observability", "retries"),
            )
        )
        if retries is not None:
            replay_values.append(retries)

        love_delta = _parse_float(
            _extract_first(
                record,
                ("love_resonance_delta",),
                ("metrics", "love_resonance_delta"),
                ("telemetry", "love_resonance_delta"),
            )
        )
        if love_delta is not None:
            love_values.append(love_delta)

        coherence = _parse_float(
            _extract_first(
                record,
                ("trinity_coherence",),
                ("system_state", "temporal_coherence"),
                ("system_state", "conceptual_clarity"),
                ("state_vectors", "temporal_coherence"),
            )
        )
        if coherence is not None:
            coherence_values.append(coherence)

    def average(values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    avg_latency = average(latency_values)
    avg_replay = average([float(v) for v in replay_values])
    avg_love = average(love_values)
    avg_coherence = average(coherence_values)

    cohesion_index = max(
        0.0,
        min(
            1.0,
            (1.0 - min(avg_latency / 10000.0, 0.8))
            - min(avg_replay / 10.0, 0.4)
            + min(avg_love / 5.0, 0.4)
            + (avg_coherence - 0.5),
        ),
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_log": str(source),
        "samples": len(records),
        "metrics": {
            "average_latency_ms": round(avg_latency, 2),
            "average_replay_count": round(avg_replay, 2),
            "average_love_resonance_delta": round(avg_love, 3),
            "average_trinity_coherence": round(avg_coherence, 3),
            "cohesion_index": round(cohesion_index, 3),
        },
    }


def _build_timeline_map(records: List[Dict[str, Any]], source: Path) -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []
    for record in records:
        timestamp = _extract_timestamp(record)
        lineage = _extract_first(record, ("lineage",), ("metadata", "lineage"))
        location = _extract_first(
            record,
            ("location",),
            ("geo",),
            ("metadata", "location"),
        )

        lat: Optional[float] = None
        lon: Optional[float] = None
        if isinstance(location, dict):
            if "coordinates" in location and isinstance(location["coordinates"], (list, tuple)):
                coords = location["coordinates"]
                if len(coords) == 2:
                    lat = _parse_float(coords[0])
                    lon = _parse_float(coords[1])
            else:
                lat = _parse_float(location.get("lat"))
                lon = _parse_float(location.get("lon"))
        elif isinstance(location, (list, tuple)) and len(location) == 2:
            lat = _parse_float(location[0])
            lon = _parse_float(location[1])
        elif isinstance(location, str):
            if "," in location:
                parts = [part.strip() for part in location.split(",")]
                if len(parts) == 2:
                    lat = _parse_float(parts[0])
                    lon = _parse_float(parts[1])

        event: Dict[str, Any] = {
            "timestamp": timestamp,
            "kairos_level": _parse_int(
                _extract_first(
                    record,
                    ("kairos_level",),
                    ("metrics", "kairos_level"),
                    ("components", "kairos", "level"),
                )
            ),
            "lineage": lineage,
            "impact": _parse_float(
                _extract_first(
                    record,
                    ("impact",),
                    ("metrics", "impact"),
                    ("components", "kairos", "impact"),
                )
            ),
            "agents": _extract_agent_tags(record),
        }

        if lat is not None and lon is not None:
            event["coordinates"] = {"lat": lat, "lon": lon}

        events.append(event)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_log": str(source),
        "events": events,
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def export_dashboards(log_path: Path, output_dir: Path) -> DashboardArtifacts:
    records = _load_log_records(log_path)
    _ensure_output_dir(output_dir)

    compass = _build_kairos_compass(records, log_path)
    cohesion = _build_cohesion_dashboard(records, log_path)
    timeline_map = _build_timeline_map(records, log_path)

    _write_json(output_dir / "kairos_compass.json", compass)
    _write_json(output_dir / "cohesion_dashboard.json", cohesion)
    _write_json(output_dir / "timeline_map.json", timeline_map)

    return DashboardArtifacts(compass, cohesion, timeline_map)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export EvoDashboard visualisations from Trinity metrics logs.")
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to logs/trinity_metrics.log (default: logs/trinity_metrics.log)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for dashboard payloads (default: EvoDashboard)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    artifacts = export_dashboards(args.log, args.output)
    summary = {
        "kairos_compass_records": artifacts.kairos_compass["records"],
        "cohesion_samples": artifacts.cohesion_dashboard["samples"],
        "timeline_events": len(artifacts.timeline_map["events"]),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
