import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.export_dashboards import export_dashboards


def _write_log(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_export_dashboards_creates_payloads(tmp_path) -> None:
    log_file = tmp_path / "trinity_metrics.log"
    timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat()

    _write_log(
        log_file,
        [
            {
                "timestamp": timestamp,
                "impact": 0.82,
                "kairos_level": 4,
                "agent_tags": ["Observer", "Scientist"],
                "latency_ms": 1200,
                "retries": 1,
                "love_resonance_delta": 0.18,
                "trinity_coherence": 0.91,
                "lineage": "lineages.kairos_bridge",
                "geo": {"lat": 55.75, "lon": 37.61},
            },
            {
                "meta": {"timestamp": timestamp, "agent_tags": "Architect"},
                "metrics": {
                    "impact": "high",
                    "kairos_level": 3,
                    "latency_ms": 600,
                    "retries": 0,
                    "love_resonance_delta": 0.05,
                },
                "system_state": {"temporal_coherence": 0.73},
                "metadata": {"lineage": "lineages.logos_loop"},
            },
            {
                "components": {
                    "kairos": {"impact": 0.28, "level": 2},
                    "chronos": {"timestamp": timestamp},
                },
                "observability": {"latency_ms": 2200, "retries": 3},
                "telemetry": {"love_resonance_delta": -0.02},
                "state_vectors": {"temporal_coherence": 0.6},
                "metadata": {"agent_tags": ["Soul"], "lineage": "lineages.soul_sync"},
            },
        ],
    )

    output_dir = tmp_path / "EvoDashboard"
    artifacts = export_dashboards(log_file, output_dir)

    compass_path = output_dir / "kairos_compass.json"
    cohesion_path = output_dir / "cohesion_dashboard.json"
    timeline_path = output_dir / "timeline_map.json"

    assert compass_path.exists()
    assert cohesion_path.exists()
    assert timeline_path.exists()

    compass = json.loads(compass_path.read_text(encoding="utf-8"))
    cohesion = json.loads(cohesion_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))

    assert compass["records"] == 3
    assert compass["skipped_records"] == 0
    assert cohesion["metrics"]["average_latency_ms"] > 0
    assert cohesion["metrics"]["cohesion_index"] >= 0
    assert len(timeline["events"]) == 3

    # Validate the returned dataclass mirrors the JSON exports.
    assert artifacts.kairos_compass["records"] == 3
    assert artifacts.cohesion_dashboard["samples"] == 3
    assert len(artifacts.timeline_map["events"]) == 3


def test_export_dashboards_handles_malformed_records(tmp_path) -> None:
    """Ensure malformed Kairos events do not break the exporter."""

    log_file = tmp_path / "trinity_metrics.log"
    timestamp = datetime(2025, 2, 2, tzinfo=timezone.utc).isoformat()

    malformed_lines = [
        json.dumps(
            {
                "timestamp": timestamp,
                "impact": 0.45,
                "kairos_level": 1,
                "latency_ms": "fast",  # ignored during numeric parsing
                "agent_tags": "Observer,Scientist",
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "timestamp": "broken",
                "impact": "n/a",
                "kairos_level": "?",
                "agents": ["Architect"],
            },
            ensure_ascii=False,
        ),
        "not-json",
        json.dumps(
            {
                "metrics": {"impact": -5, "kairos_level": 3},
                "observability": {"latency_ms": 9999, "retries": 6},
                "metadata": {"agent_tags": ["Scientist"]},
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "meta": {"timestamp": timestamp},
                "components": {"kairos": {"impact": 120, "level": 5}},
                "location": ["55.7", "37.6"],
                "love_resonance_delta": "0.33",
            },
            ensure_ascii=False,
        ),
    ]

    log_file.write_text("\n".join(malformed_lines) + "\n", encoding="utf-8")

    artifacts = export_dashboards(log_file, tmp_path / "EvoDashboard")

    compass = artifacts.kairos_compass
    timeline = artifacts.timeline_map
    cohesion = artifacts.cohesion_dashboard

    # Only entries with usable impact and Kairos level values are counted.
    assert compass["records"] == 3
    assert compass["skipped_records"] == 1

    impacts = {event["impact"] for event in compass["events"]}
    assert 0.0 in impacts  # negative values are clamped to 0.0
    assert 1.0 in impacts  # large values are normalised into [0, 1]

    # Timeline should include every successfully parsed JSON record, even if partial.
    assert len(timeline["events"]) == 4
    assert any("coordinates" in event for event in timeline["events"])

    # Cohesion dashboard gracefully ignores malformed numeric fields.
    metrics = cohesion["metrics"]
    assert metrics["average_latency_ms"] == 9999.0
    assert 0.0 <= metrics["cohesion_index"] <= 1.0


def test_export_dashboards_handles_nested_collections_and_encodings(tmp_path) -> None:
    timestamp = datetime(2025, 3, 3, tzinfo=timezone.utc).isoformat()

    log_file = tmp_path / "trinity_metrics.log"
    _write_log(
        log_file,
        [
            {
                "meta": {"timestamp": timestamp, "agent_tags": [["Observer"], ["Scientist", "Soul"]]},
                "metrics": [
                    {"impact": {"value": "85%"}},
                    {"kairos_level": "4"},
                    {"latency_ms": "1,200"},
                    {"retries": {"value": "2"}},
                    {"love_resonance_delta": ["0,15", {"fallback": 0.12}]},
                ],
                "system_state": [
                    {"temporal_coherence": "0,78"},
                    {"conceptual_clarity": "0.81"},
                ],
                "location": {"coordinates": ["55,75°N", "37,61°E"]},
                "metadata": {"lineage": "lineages.nested"},
            }
        ],
    )

    artifacts = export_dashboards(log_file, tmp_path / "EvoDashboard")

    compass = artifacts.kairos_compass
    timeline = artifacts.timeline_map
    cohesion = artifacts.cohesion_dashboard

    assert compass["records"] == 1
    assert compass["events"][0]["impact"] == 0.85
    assert compass["events"][0]["kairos_level"] == 4
    assert set(compass["events"][0]["agent_tags"]) == {"Observer", "Scientist", "Soul"}

    metrics = cohesion["metrics"]
    assert metrics["average_latency_ms"] == 1200.0
    assert metrics["average_replay_count"] == 2.0
    assert metrics["average_love_resonance_delta"] == 0.15
    assert metrics["average_trinity_coherence"] == 0.78

    event = timeline["events"][0]
    assert event["lineage"] == "lineages.nested"
    assert event["coordinates"] == {"lat": 55.75, "lon": 37.61}


def test_export_dashboards_real_world_capture_fixture(tmp_path) -> None:
    """Validate exporter against a captured Kairos Compass telemetry snapshot."""

    fixture_path = Path(__file__).resolve().parent / "data" / "kairos_compass_capture_20241221.jsonl"
    log_file = tmp_path / "trinity_metrics.log"
    log_file.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    artifacts = export_dashboards(log_file, tmp_path / "EvoDashboard")

    compass = artifacts.kairos_compass
    assert compass["records"] == 3
    assert compass["skipped_records"] == 0
    assert compass["matrix"]["3"]["high"]["count"] == 1
    assert compass["matrix"]["2"]["mid"]["count"] == 1

    cohesion = artifacts.cohesion_dashboard["metrics"]
    assert cohesion["average_latency_ms"] == pytest.approx(1464.67, abs=0.01)
    assert cohesion["average_replay_count"] == pytest.approx(1.33, abs=0.01)
    assert cohesion["average_love_resonance_delta"] == pytest.approx(0.143, abs=0.001)
    assert cohesion["average_trinity_coherence"] == pytest.approx(0.847, abs=0.001)
    assert cohesion["cohesion_index"] == 1.0

    timeline_events = artifacts.timeline_map["events"]
    assert len(timeline_events) == 3
    lineages = {event["lineage"] for event in timeline_events}
    assert {"lineages.kairos_bridge", "lineages.logos_bridge", "lineages.memory_wave"} <= lineages

    coords = [event["coordinates"] for event in timeline_events if "coordinates" in event]
    assert any(pytest.approx(55.7534, abs=1e-4) == coord["lat"] for coord in coords)
    assert any(pytest.approx(37.6216, abs=1e-4) == coord["lon"] for coord in coords)

    logos_tags = next(event["agents"] for event in timeline_events if event["lineage"] == "lineages.logos_bridge")
    assert set(logos_tags) == {"Architect", "Philosopher"}
