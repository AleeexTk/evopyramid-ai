"""Общие зависимости для FastAPI слоя."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from apps.core.memory.memory_manager import Memory


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Валидация API ключа через Memory Manager."""

    valid_keys = await Memory.get("api_keys") or []
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    return x_api_key


__all__ = ["verify_api_key"]
