from __future__ import annotations
from typing import Dict, Any
import os, json, time

def _evodir() -> str:
    d = os.environ.get("EVODIR")
    if d: return d
    return "./local_EVO" if not os.path.exists("/storage/emulated/0") else "/storage/emulated/0/Download/EVO"

class FlowMonitor:
    """
    Записывает простые метрики «потока» в JSONL.
    Метрики: coherence, novelty, soul_resonance, latency, density.
    """
    def __init__(self, name="collective_flow"):
        self.dir = os.path.join(_evodir(), "logs")
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, f"{name}.jsonl")

    def log(self, metrics: Dict[str, Any]) -> None:
        metrics = dict(metrics)
        metrics["ts"] = time.time()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    @staticmethod
    def compute_coherence(text: str) -> float:
        # грубая эвристика: длиннее и структурированнее → выше
        return max(0.1, min(1.0, len(text)/800.0))

    @staticmethod
    def compute_novelty(context: Dict[str,Any]) -> float:
        return 0.5 + 0.5*min(1.0, len(str(context.get("memory",{})))/400.0)

