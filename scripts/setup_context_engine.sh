#!/bin/bash
set -euo pipefail

log() {
  echo "[setup] $*"
}

log "🚀 Установка Quantum Context Engine"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
log "📁 Корневая директория проекта: $PROJECT_ROOT"

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

log "🔄 Обновляем pip"
python -m pip install --upgrade pip

declare -a REQUIREMENTS_FILES=("requirements.txt" "requirements_context.txt")
found_requirements=false
for req_file in "${REQUIREMENTS_FILES[@]}"; do
  if [ -f "$req_file" ]; then
    found_requirements=true
    log "📦 Устанавливаем зависимости из $req_file"
    python -m pip install -r "$req_file"
  else
    log "⚠️ $req_file не найден, пропускаем"
  fi
done

if [ "$found_requirements" = false ]; then
  echo "❌ Не найдены файлы зависимостей (requirements.txt или requirements_context.txt)" >&2
  exit 1
fi

log "🔍 Проверяем установку ключевых пакетов"
missing_packages=()
for package in pytest pytest_asyncio aiofiles xmltodict; do
  if ! python -c "import $package" >/dev/null 2>&1; then
    missing_packages+=("$package")
  fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
  echo "❌ Не удалось установить пакеты: ${missing_packages[*]}" >&2
  exit 1
fi

log "📁 Проверяем структуру Quantum Context Engine"
for component in \
  apps/core/context/quantum_analyzer.py \
  apps/core/memory/pyramid_memory.py \
  apps/core/integration/context_engine.py \
  tests/context/test_quantum_analyzer.py \
  tests/context/test_pyramid_memory.py; do
  if [ ! -f "$component" ]; then
    echo "❌ Не найден компонент $component" >&2
    echo "Запустите scripts/integrate_quantum_context.sh перед установкой" >&2
    exit 1
  fi
done

log "🧪 Запускаем тесты Quantum Context Engine"
set +e
python -m pytest tests/context/ -v
test_status=$?
set -e

if [ $test_status -eq 0 ]; then
  log "✅ Все тесты прошли успешно"
else
  log "⚠️ Тесты завершились с ошибками (код $test_status)"
fi

log "🎯 Запуск демонстрации Quantum Context Engine"
set +e
python - <<'PYCODE'
import asyncio
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

spec = importlib.util.find_spec("apps.core.integration.context_engine")
if spec is None:
    print("❌ Модуль apps.core.integration.context_engine не найден")
else:
    module = importlib.import_module("apps.core.integration.context_engine")
    demo_integration = getattr(module, "demo_integration", None)
    if demo_integration is None:
        print("❌ Функция demo_integration отсутствует в модуле")
    else:
        try:
            asyncio.run(demo_integration())
        except Exception as exc:  # noqa: BLE001 - информируем пользователя
            print(f"❌ Ошибка демонстрации: {exc}")
PYCODE
demo_status=$?
set -e

if [ $demo_status -eq 0 ]; then
  log "✅ Демонстрация завершена успешно"
else
  log "⚠️ Демонстрация завершилась с ошибками (код $demo_status)"
fi

if [ ! -f "evo_config.json" ]; then
  log "⚙️ Создаём базовую конфигурацию evo_config.json"
  cat >evo_config.json <<'JSON'
{
  "system": {
    "name": "EvoPyramid-AI",
    "version": "1.0.0",
    "creator": "AlexCreator"
  },
  "components": {
    "quantum_context_engine": {
      "enabled": true,
      "auto_analyze": true
    },
    "pyramid_memory": {
      "enabled": true
    }
  }
}
JSON
fi

log "🎉 Установка завершена"
log "Документация: docs/integration/QUANTUM_CONTEXT_INTEGRATION.md"
