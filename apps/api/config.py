"""Конфигурация производственного API слоя EvoPyramid."""

from __future__ import annotations

from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """Конфигурация API для разных профилей запуска."""

    environment: Literal["local", "termux", "cloud"] = "local"
    api_version: str = "v1"
    debug: bool = False

    # Безопасность
    jwt_secret: str = "dev-secret"
    api_rate_limit: str = "100/minute"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    trusted_hosts: List[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "testserver",
            "evopyramid.com",
            "api.evopyramid.com",
        ]
    )

    # Мониторинг
    metrics_enabled: bool = True
    health_check_interval: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = APISettings()

__all__ = ["APISettings", "settings"]
