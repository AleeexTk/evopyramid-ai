"""CLI для запуска FastAPI приложения."""

from __future__ import annotations

import uvicorn

from .config import settings
from .main import app


def start_server() -> None:
    """Запуск production сервера."""

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        access_log=True,
    )


if __name__ == "__main__":  # pragma: no cover - ручной запуск
    start_server()
