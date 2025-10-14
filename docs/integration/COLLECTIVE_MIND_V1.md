# COLLECTIVE_MIND_v1

Минимально-жизнеспособный «коллективный разум» EvoPyramid:

- **IntentStreamClassifier** — предклассификация (FLOOD/TECHNICAL/PHILOSOPHICAL/CREATIVE/META)
- **ContextEngine** — твой существующий анализ контекста (QuantumContext + PyramidMemory)
- **AGI-proto roles** — роли Absolut / Archivarius / Evochka генерируют предложения
- **ConsensusEngine** — взвешенное решение (gold/platinum/standard)
- **FlowMonitor** — метрики потока (coherence/novelty/soul_resonance/latency/density)

## Запуск

### Через PEAR-ритуал
```
EVO/PEAR> rituals
EVO/PEAR> meta_agi
EVO/PEAR> show_flow
```

### Напрямую
```bash
python3 apps/cli/collective_mind_cli.py "Разработай архитектуру моста между ядрами"
```

## Как это работает
1. Классификатор помечает «флуд» и отсекает его от тяжёлой логики.
2. ContextEngine строит слои intent/affect/memory и выдаёт приоритетный путь.
3. Роли дают предложения (stance + rationale + payload).
4. ConsensusEngine считает score и решает: evolve/approve/modify/reject (platinum/gold/standard).
5. FlowMonitor пишет метрики в `EVODIR/logs/collective_flow.jsonl` (или `./local_EVO/...`).

## Расширение
- Добавляй новые роли в `apps/core/agi_proto/roles.py`
- Меняй веса/пороги в `apps/core/consensus/consensus_engine.py`
- Интегрируй в EvoNexusBridge для многоядерных дискуссий

