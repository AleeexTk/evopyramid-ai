from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .nexus import EvoNexusBridge


class WatcherOmegaBridge:
    """
    Лёгкий адаптер под будущий EvoGrapeshot:
    - смотрит в каталог signals/
    - находит *.trigger/*.json
    - пробрасывает предложение в EvoNexusBridge
    """

    def __init__(self, signals_dir: Optional[str] = None) -> None:
        self.signals_dir = signals_dir or "./signals"
        os.makedirs(self.signals_dir, exist_ok=True)
        self.nexus = EvoNexusBridge()

    async def run_once(self, session_id: str = "PEAR_A24") -> Dict[str, Any]:
        files = [f for f in os.listdir(self.signals_dir) if f.endswith(".json") or f.endswith(".trigger")]
        if not files:
            return {"ok": True, "message": "No signals"}
        fname = sorted(files)[0]
        path = os.path.join(self.signals_dir, fname)
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except Exception:
                file.seek(0)
                data = {"proposal": file.read()}
        os.remove(path)

        proposal = data.get("proposal") or data.get("content") or "Общее улучшение интеграции"
        return await self.nexus.run(proposal=proposal, session_id=session_id)
