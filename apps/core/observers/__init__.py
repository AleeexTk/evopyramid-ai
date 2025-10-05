"""Observer modules for EvoPyramid systems."""

from importlib import import_module
from typing import TYPE_CHECKING

__all__ = [
    "ChronosStream",
    "KairosDetector",
    "MnemosyneArchiver",
    "ObserverMode",
    "TrinityObserver",
    "TrinityState",
    "initialize_trinity_observer",
    "shutdown_trinity_observer",
    "trinity_observer",
]

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .trinity_observer import (
        ChronosStream,
        KairosDetector,
        MnemosyneArchiver,
        ObserverMode,
        TrinityObserver,
        TrinityState,
        initialize_trinity_observer,
        shutdown_trinity_observer,
        trinity_observer,
    )


def __getattr__(name):
    if name in __all__:
        module = import_module("apps.core.observers.trinity_observer")
        return getattr(module, name)
    raise AttributeError(f"module 'apps.core.observers' has no attribute '{name}'")
