"""Codex-centric endpoints for EvoPyramid API."""

from __future__ import annotations

from typing import Iterable, List

from api.schemas.base import CodeReviewRequest
from api.schemas.response import ReviewInsight


def evaluate_code(payload: CodeReviewRequest) -> List[ReviewInsight]:
    """Produce structured review insights.

    The logic intentionally remains lightweight; real evaluation is delegated to
    Codex laboratories. This function shapes the payload for downstream
    processing.
    """

    insights: List[ReviewInsight] = []
    for issue in _detect_surface_issues(payload):
        insights.append(
            ReviewInsight(
                severity=issue["severity"],
                message=issue["message"],
                file_path=issue.get("file_path"),
                metadata={"source": "codex-scan"},
            )
        )
    if not insights:
        insights.append(
            ReviewInsight(
                severity="info",
                message="No static issues detected; escalate to Codex deep review.",
                metadata={"source": "codex-scan"},
            )
        )
    return insights


def _detect_surface_issues(payload: CodeReviewRequest) -> Iterable[dict[str, str]]:
    """Perform a minimal heuristic scan of the diff summary."""

    for snippet in payload.diff_snippets:
        if "TODO" in snippet.text:
            yield {
                "severity": "warning",
                "message": "TODO markers should be resolved or ticketed.",
                "file_path": snippet.file_path,
            }
        if "print(" in snippet.text:
            yield {
                "severity": "warning",
                "message": "Debug print detected; ensure logging policy compliance.",
                "file_path": snippet.file_path,
            }
