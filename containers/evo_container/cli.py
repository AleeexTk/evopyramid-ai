"""Command helpers for Evo Container pipelines."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Mapping, MutableMapping

from . import adapt, analysis, harmonize, intake, integrate, syncer
from .evo_link_bridge.narrator import processor as narrator_processor

PipelineStep = Callable[[MutableMapping[str, object]], MutableMapping[str, object]]


PIPELINES: Dict[str, Iterable[PipelineStep]] = {
    "link_import_to_memory": (
        intake.collect_link,
        analysis.analyze_link,
        adapt.adapt_for_memory,
        integrate.integrate_payload,
        syncer.sync_memory,
        harmonize.harmonize_state,
        narrator_processor.create_chronicle,
    )
}


def run_pipeline(name: str, initial_state: Mapping[str, object]) -> Dict[str, object]:
    """Execute a named pipeline with the provided initial state."""

    if name not in PIPELINES:
        raise KeyError(f"Unknown pipeline '{name}'")

    state: MutableMapping[str, object] = dict(initial_state)
    for step in PIPELINES[name]:
        state = step(state)  # type: ignore[assignment]
    return dict(state)


__all__ = ["PIPELINES", "run_pipeline"]
