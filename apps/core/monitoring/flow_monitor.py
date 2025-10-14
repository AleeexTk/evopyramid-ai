from __future__ import annotations
from typing import Dict, Any, Callable
import os
import json
import time


TempoHandler = Callable[[float], None]
StateHandler = Callable[[Any], None]


def _evodir() -> str:
    directory = os.environ.get("EVODIR")
    if directory:
        return directory
    return "./local_EVO" if not os.path.exists("/storage/emulated/0") else "/storage/emulated/0/Download/EVO"


class FlowMonitor:
    """
    Записывает простые метрики «потока» в JSONL.
    Метрики: coherence, novelty, soul_resonance, latency, density.
    """

    _tempo_handlers: list[TempoHandler] = []
    _state_handlers: list[StateHandler] = []
    _last_flow: Dict[str, Any] = {"coherence": 0.5, "soul_resonance": 0.5}

    def __init__(self, name: str = "collective_flow") -> None:
        self.dir = os.path.join(_evodir(), "logs")
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, f"{name}.jsonl")

    def log(self, metrics: Dict[str, Any]) -> None:
        metrics = dict(metrics)
        metrics["ts"] = time.time()
        FlowMonitor.update_flow(**metrics)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    @staticmethod
    def compute_coherence(text: str) -> float:
        # грубая эвристика: длиннее и структурированнее → выше
        return max(0.1, min(1.0, len(text) / 800.0))

    @staticmethod
    def compute_novelty(context: Dict[str, Any]) -> float:
        return 0.5 + 0.5 * min(1.0, len(str(context.get("memory", {}))) / 400.0)

    @classmethod
    def get_current_flow(cls) -> Dict[str, Any]:
        return dict(cls._last_flow)

    @classmethod
    def update_flow(cls, **kwargs: Any) -> None:
        cls._last_flow.update(kwargs)

    @classmethod
    def register_tempo_handler(cls, handler: TempoHandler) -> None:
        cls._tempo_handlers.append(handler)

    @classmethod
    def register_state_handler(cls, handler: StateHandler) -> None:
        cls._state_handlers.append(handler)

    @classmethod
    def suggest_tempo(cls, value: float) -> None:
        for handler in list(cls._tempo_handlers):
            try:
                handler(value)
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[FlowMonitor] tempo handler error: {exc}")

    @classmethod
    def suggest_state(cls, state: Any) -> None:
        for handler in list(cls._state_handlers):
            try:
                handler(state)
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[FlowMonitor] state handler error: {exc}")
