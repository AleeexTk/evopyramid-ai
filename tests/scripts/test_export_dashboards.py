import json
from datetime import datetime, timezone
from pathlib import Path

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
