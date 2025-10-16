"""Asynchronous in-memory store used by EvoPyramid tests and services."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional


class _ProjectMemory:
    def __init__(self, base: str) -> None:
        self.base = base
        os.makedirs(self.base, exist_ok=True)

    async def flush(self) -> None:
        await asyncio.sleep(0)


class Memory:
    """In-memory key/value store with a lightweight async interface."""

    _store: Dict[str, Any] = {
        "api_keys": ["dev-api-key"],
        "self_evolving_skills": {},
    }
    _lock = asyncio.Lock()


    @staticmethod
    def for_project(project: str) -> _ProjectMemory:
        base = os.path.join("EvoMemory", project)
        return _ProjectMemory(base=base)

    @classmethod
    async def get(cls, key: str, default: Optional[Any] = None) -> Any:
        async with cls._lock:
            return cls._store.get(key, default)

    @classmethod
    async def set(cls, key: str, value: Any) -> None:
        async with cls._lock:
            cls._store[key] = value

    @classmethod
    async def find_similar(cls, sample: Any, threshold: float = 0.8) -> List[Any]:
        del sample, threshold
        async with cls._lock:
            history = cls._store.get("context_history", [])
            return history[-3:]

    @classmethod
    async def save_state(
        cls, key: str, value: Any, *, category: str | None = None
    ) -> None:
        async with cls._lock:
            if category:
                bucket = cls._store.setdefault(category, {})
                bucket[key] = value
            else:
                cls._store[key] = value

    @classmethod
    async def append_history(cls, entry: Any) -> None:
        async with cls._lock:
            history = cls._store.setdefault("context_history", [])
            history.append(entry)

    @classmethod
    async def ping(cls) -> bool:
        async with cls._lock:
            return True


__all__ = ["Memory"]
