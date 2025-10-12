# EvoNexusBridge + Consensus Engine

Коллективный разум между ядрами через три шага:

1) **DataAssimilationNexus** — собирает контекст (intent/affect/memory) из `QuantumContextAnalyzer / ContextEngine`.
2) **CognitiveFusionMatrix** — синтезирует инсайт и «творческий» выход (набор шагов/план).
3) **ConsensusEngine** — голосование ядер (EvoKernel/ExEvo/Evo24/Codex) с весами, пороги:
   - `gold` ≥ 0.75 → approve
   - `platinum` ≥ 0.9 → evolve

## Запуск

CLI:
```bash
python apps/cli/evo_nexus_cli.py --proposal "Рефракция ролей" --session PEAR_A24
```

EvoCodexShell (ритуал):
```text
EVO/PEAR> run ritual nexus_discuss "Рефракция ролей"
```

Артефакты сохраняются в `EVODIR/nexus_logs/*.json` (по умолчанию `./local_EVO` вне Termux).

## Расширение
- Подключить реальный Grapeshot Watcher через `apps/bridge/evonexus/grapeshot_adapter.py`
- Уточнить веса ядер и правила голосования
- Добавить экспорт в EvoMETA Kairos-лог

## Связанные документы
- `docs/integration/QUANTUM_CONTEXT_INTEGRATION.md`
- `docs/EVO_COLLAB_GUIDE.md`
- `docs/EVO_SUMMON.md`
