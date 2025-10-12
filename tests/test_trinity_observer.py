import pytest

from apps.core.observers.trinity_observer import (
    ObserverMode,
    TrinityObserver,
    initialize_trinity_observer,
    shutdown_trinity_observer,
)


@pytest.mark.asyncio
async def test_trinity_observer_initialize_and_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    observer = TrinityObserver()
    await observer.start_observation()
    state = await observer.get_current_state()
    assert state["observer_mode"] == ObserverMode.ACTIVE_MONITORING.value
    await observer.stop_observation()


@pytest.mark.asyncio
async def test_global_trinity_observer_lifecycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    observer = await initialize_trinity_observer()
    state = await observer.get_current_state()
    assert "statistics" in state
    await shutdown_trinity_observer()
