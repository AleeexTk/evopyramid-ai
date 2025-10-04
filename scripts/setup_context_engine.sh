#!/bin/bash
set -euo pipefail

log() {
  echo "[setup] $*"
}

log "🚀 Установка Quantum Context Engine"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 не установлен" >&2
  exit 1
fi
log "✅ Обнаружен Python $(python3 --version)"

if [ ! -d ".venv" ]; then
  log "📦 Создаём виртуальное окружение..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
log "✅ Виртуальное окружение активно"

if [ -f "requirements.txt" ]; then
  log "📥 Устанавливаем зависимости из requirements.txt"
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
else
  log "⚠️ requirements.txt не найден, пропускаем установку зависимостей"
fi

log "📁 Проверяем структуру проекта"
for path in apps/core/context apps/core/memory apps/core/integration; do
  if [ ! -d "$path" ]; then
    echo "❌ Не найдена директория $path" >&2
    exit 1
  fi
done

log "🧪 Запуск тестов"
python -m pytest tests/context/test_quantum_analyzer.py -v
python -m pytest tests/context/test_pyramid_memory.py -v

log "🎯 Запуск демонстрации"
python - <<'PYCODE'
import asyncio
from apps.core.integration.context_engine import demo_integration

asyncio.run(demo_integration())
PYCODE

log "🎉 Установка завершена"
log "Документация: docs/integration/QUANTUM_CONTEXT_INTEGRATION.md"
