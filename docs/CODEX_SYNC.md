# Codex Sync (Evo ↔ Codex)

Этот контур превращает Codex в «живой» ревьюер, а Trinity — в память и монитор эволюции.

## Потоки

1) Разработка → `codex-review`
2) GitHub Actions (`codex-sync.yml`) прогоняет линт/тесты и создаёт PR → `main`
3) Логи пишутся в `logs/codex_feedback.log`
4) `apps/core/trinity_observer.py` периодически читает логи и сохраняет отчёт в `codex_feedback/`

## Быстрый старт

```bash
# однажды:
git checkout -b codex-review
git push origin codex-review
# включи Actions и дай им права (Settings → Actions → Allow all actions)

Локальный цикл

# Termux
bash scripts/start_termux.sh

# VS Code / Windows
PowerShell> scripts/start_local.sh
```

Просмотр статуса

Последние 10 строк фидбэка Codex — в отчёте Trinity (`codex_feedback/*.json`)

Подробный лог — `logs/codex_feedback.log`

Авто-PR → вкладка Pull Requests (label: codex,autosync)
