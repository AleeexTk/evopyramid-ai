"""Backward-compatible entrypoint for the Trinity Observer."""

from apps.core.observers.trinity_observer import (  # noqa: F401
    ChronosStream,
    KairosDetector,
    MnemosyneArchiver,
    ObserverMode,
    TrinityObserver,
    TrinityState,
    initialize_trinity_observer,
    main,
    shutdown_trinity_observer,
    trinity_observer,
)

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

if __name__ == "__main__":
    main()
