# EvoPyramid API — Ethics & Conduct Protocol

## Guiding Principles
1. **Transparency** — Все вызовы регистрируются Trinity Observer'ом и доступны для аудита Codex'ом.
2. **Reversibility** — Любое действие должно быть отзывным до фиксации в внешней среде.
3. **Coherence First** — Если взаимодействие снижает эмоциональную или смысловую когерентность, оно блокируется.
4. **Respectful Dialogue** — Внешние агенты проходят согласование через EvoBridge Agreements и подтверждают принятие этического слоя.

## Operational Policy
- Хранить журналы во `logs/trinity_metrics.log` и `EvoMemory/`.
- Использовать `api/manifest.yaml` как единственный источник правды по маршрутам.
- Любые расширения требуют обновления `EVO_ARCH_MAP.yaml` и синхронизации с `EVO_SYNC_MANIFEST.yaml`.

## Incident Response
- Триггером служит снижение показателя coherence < 0.85.
- Trinity Observer инициирует `reflective_synthesis` и сообщает Codex.
- Codex проводит аудит маршрутов и, при необходимости, активирует EvoLock.

## External Collaboration
- Подписывать `EvoBridge Agreement` перед доступом к защищённым маршрутам.
- Применять двустороннее шифрование (EvoKeyCore).
- Фиксировать контекст в EvoMemory как Kairos-моменты с указанием источника.

Этика = структурная целостность + эмоциональная гармония.
