# Руководство по запуску EvoPyramid в Termux

Это пошаговая инструкция, которая показывает, как превратить устройство с Termux и плагином Termux:Boot в штатный узел архитектуры EvoPyramid. Руководство ориентировано на свежую установку Termux и охватывает как подготовку окружения, так и подключение нового Python-рантайма.

## 1. Предварительная подготовка Termux

1. Откройте Termux и обновите пакеты:
   ```bash
   pkg update && pkg upgrade
   ```
2. Установите необходимые зависимости:
   ```bash
   pkg install git python openssh
   ```
3. (Опционально) Разрешите Termux доступ к внешнему хранилищу:
   ```bash
   termux-setup-storage
   ```

## 2. Размещение репозитория EvoPyramid

По умолчанию архитектура размещает рабочее дерево в домашнем каталоге Termux (`$HOME/evopyramid-ai`). Это избавляет от ошибки `detected dubious ownership`, которая возникает при работе с `/storage/emulated/0`.

1. Если у вас уже есть копия на внешнем хранилище (`/storage/emulated/0/EVO_LOCAL/evopyramid-ai`), ничего переносить не нужно — новый рантайм мигрирует её автоматически.
2. Если копии нет, просто клонируйте репозиторий:
   ```bash
   git clone https://github.com/AleeexTk/evopyramid-ai.git
   ```
3. Проверьте, что Python-окружение запускается:
   ```bash
   cd ~/evopyramid-ai
   python3 -m compileall core/runtime
   ```

## 3. Установка скрипта автозапуска Termux:Boot

1. Убедитесь, что установлен плагин [Termux:Boot](https://github.com/termux/termux-boot).
2. Скопируйте скрипт из репозитория в директорию автозапуска:
   ```bash
   mkdir -p ~/.termux/boot
   cp ~/evopyramid-ai/scripts/termux_boot_autostart.sh ~/.termux/boot/start-evopyramid.sh
   chmod 755 ~/.termux/boot/start-evopyramid.sh
   ```
3. При необходимости скорректируйте переменные в начале файла:
   - `EVO_PARENT_DIR` — базовая директория, где будет храниться репозиторий и логи.
   - `PY_ENV` — путь к нужной версии Python (оставьте по умолчанию, если используете системный `python3`).
   - `ENTRY_POINT` — модуль EvoPyramid, который нужно запустить после синхронизации (по умолчанию `apps.core.trinity_observer`).

## 4. Что делает скрипт при старте

1. Создаёт папку логов `~/logs/termux_boot` (или в директории, указанной через `LOG_DIR`).
2. Проверяет наличие репозитория:
   - Если папка существует, но файл `core/runtime/main.py` отсутствует, выполняет `git fetch` + `git reset --hard` для восстановления.
   - Если репозитория нет, выполняет `git clone` в `LOCAL_DIR`.
3. Экспортирует набор переменных `EVO_RUNTIME_*`, которые настраивают Python-рантайм.
4. При наличии старых копий из `/storage/emulated/0/...` передаёт их путём `EVO_RUNTIME_MIGRATE_SOURCES` для автоматической миграции.
5. Запускает Python-скрипт `core/runtime/main.py --environment termux`, который:
   - Регистрирует `git config --global --add safe.directory ...`, чтобы устранить ошибку `dubious ownership`.
   - Выполняет полный цикл `git fetch` → `git stash` → `git reset --hard` → `git stash pop` → `git push --force-with-lease` (если есть изменения).
   - Захватывает и отпускает wake-lock через `termux-wake-lock` / `termux-wake-unlock`.
   - Стартует модуль EvoPyramid (`python -m apps.core.trinity_observer`) в новом фоне.
6. Все события логируются в файл `~/logs/termux_boot/boot-<дата>.log`.

## 5. Ручной тест перед автозапуском

1. Выполните скрипт вручную, чтобы убедиться, что всё работает:
   ```bash
   ~/.termux/boot/start-evopyramid.sh
   ```
2. После завершения проверьте статус репозитория:
   ```bash
   cd ~/evopyramid-ai
   git status
   ```
3. Ознакомьтесь с логом `~/logs/termux_boot/boot-<дата>.log` — в нём отображается весь ход синхронизации и запуск модуля.

## 6. Типовые проблемы и решения

| Симптом | Решение |
| --- | --- |
| `git: detected dubious ownership` | Рантайм автоматически добавляет `safe.directory`, но если ошибка остаётся, выполните `git config --global --add safe.directory "$(pwd)"` вручную. |
| Нет доступа к `/storage/emulated/0` | Убедитесь, что запускали `termux-setup-storage`, или измените `EVO_RUNTIME_MIGRATE_SOURCES`, чтобы исключить эту директорию. |
| Python не найден | Проверьте переменную `PY_ENV` и наличие пакета `python`. |
| Запущенный модуль завершается после старта | Проверьте лог. Если Android отключает процесс, добавьте исключение для Termux в настройках энергосбережения. |

## 7. Дополнительная настройка

- **Отключение автокоммита/пуша**: установите `export EVO_RUNTIME_PUSH_CHANGES=false` перед запуском Python-рантайма, если хотите, чтобы Termux узел никогда не отправлял изменения на GitHub.
- **Пользовательский модуль**: измените `ENTRY_POINT`, например на `apps.core.trinity_scientist`, чтобы запускать другой компонент архитектуры.
- **Сторонние зависимости**: установите их в виртуальном окружении и задайте `PY_ENV` на путь к нужному интерпретатору.

## 8. Проверка после перезагрузки

1. Перезагрузите устройство или вручную остановите/запустите Termux:Boot.
2. После загрузки убедитесь, что процесс EvoPyramid активен:
   ```bash
   ps -A | grep python
   ```
3. Просмотрите свежий лог в `~/logs/termux_boot/` и убедитесь, что синхронизация прошла без ошибок.

Следуя этим шагам, вы интегрируете Termux-устройство в EvoPyramid как полноценный узел, сохраняя синхронизацию с центральным репозиторием и управление через новый Python-рантайм.
