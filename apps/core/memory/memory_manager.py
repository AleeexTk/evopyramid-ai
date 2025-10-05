import os
import json
import asyncio
from typing import Dict, Any


class _ProjectMemory:
    def __init__(self, base: str) -> None:
        self.base = base
        os.makedirs(self.base, exist_ok=True)

    async def flush(self) -> None:
        await asyncio.sleep(0)


class Memory:
    @staticmethod
    def for_project(project: str) -> _ProjectMemory:
        return _ProjectMemory(base=os.path.join("EvoMemory", project))

    @staticmethod
    async def save_state(key: str, data: Dict[str, Any], category: str = "general") -> None:
        path = os.path.join("EvoMemory", category)
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{key}.json")
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
