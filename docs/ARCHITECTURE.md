# EvoPyramid Architecture v2.0

## Ролевая триада и граф исполнения

### Soul → Trailblazer → Provocateur: Контракт ответственности

```mermaid
graph TB
    A[Входной интент] --> B{Soul Node}
    B --> C[Архитектурный дизайн]
    C --> D[QuantumContext формирование]
    D --> E{Trailblazer Node}
    E --> F[Оптимизация потоков]
    F --> G[Маршрутизация контекста]
    G --> H{Provocateur Node}
    H --> I[Проверка безопасности]
    I --> J[Валидация границ]
    J --> K[Выходной ответ]
    
    B --> L[Context Engine]
    E --> L
    H --> L
    L --> M[Memory Manager]
    L --> N[Flow Monitor]
    L --> O[Trinity Observer]
    
    subgraph "Внешние API-узлы"
        P[JSONCrack Visualizer]
        Q[Pyramid_JSON API]
        R[Security Monitor]
    end
    
    K --> P
    K --> Q
    J --> R
```

Stateful граф исполнения (LangGraph-совместимый)

```mermaid
stateDiagram-v2
    [*] --> QuantumContext
    QuantumContext --> SoulDesign : интент принят
    SoulDesign --> TrailblazerRoute : архитектура готова
    TrailblazerRoute --> ProvocateurCheck : потоки оптимизированы
    ProvocateurCheck --> MemoryPersist : безопасно
    ProvocateurCheck --> SoulDesign : нужна доработка
    MemoryPersist --> TrinityObserve : состояние сохранено
    TrinityObserve --> [*] : цикл завершен
    
    note right of ProvocateurCheck
        Проверки безопасности:
        - JWT/API ключи
        - Rate limiting  
        - Контекстные границы
        - Инъекционные угрозы
    end note
```

## API контракты и интеграции

### JSONCrack визуализация узлов

```yaml
api_endpoints:
  /api/push:
    method: POST
    roles: [Soul, Trailblazer]
    security: JWT + Context-Signature
  
  /api/pull: 
    method: GET
    roles: [All]
    security: API-Key + TLS
  
  /api/status:
    method: GET
    roles: [Provocateur, Monitor]
    security: Internal-Only
```

### Pyramid_JSON производственный стэк

```json
{
  "production_stack": {
    "api_framework": "FastAPI + OpenAPI",
    "security_layers": ["JWT", "TLS", "OWASP_ZAP"],
    "monitoring": ["Datadog", "Prometheus", "Health_Checks"],
    "deployment": "Docker + Kubernetes",
    "config_profiles": ["local", "termux", "cloud"]
  }
}
```

### EvoContext Split Protocol (ECSP)

| Поверхность | Tier               | Роль по умолчанию                           | Лог-категория     |
| ----------- | ------------------ | ------------------------------------------- | ----------------- |
| Termux      | Runtime-Mobile     | Trinity Observer, локальные CI-проверки     | `runtime-mobile`  |
| Desktop     | Dev-Workstation    | Архитектурное редактирование и Codex-потоки | `dev-desktop`     |
| Cloud       | CI/CD Synchronizer | Автоматизированные пайплайны и отчёты       | `sync-cloud`      |

ECSP описан в `EVO_CONTEXT_MATRIX.yaml` и синхронизируется с секцией
`environment_matrix` внутри `EVO_SYNC_MANIFEST.yaml`. Перед выполнением
ритуалов Codex и Trinity вызывается `scripts/evo_context_detector.py`,
который определяет активную поверхность и экспортирует переменную
`EVO_ACTIVE_SURFACE`. Это гарантирует, что Termux-узлы остаются лёгкими,
Desktop-узлы получают права на архитектурные изменения, а Cloud-пайплайны
сфокусированы на CI/CD и публикации артефактов.

## Безопасность как первоклассная роль

### Provocateur Security Matrix

| Угроза                | Защита               | Мониторинг           |
| --------------------- | -------------------- | -------------------- |
| API инъекции          | Context-валидация    | Real-time алерты     |
| Неавторизованный доступ | JWT + RBAC         | Audit логи           |
| Перегрузка системы    | Rate limiting        | Metrics дашборд      |
| Утечки данных         | TLS + шифрование     | Trinity Observer     |

---

Документ актуализирован под индустриальные стандарты 2025.

## Исследовательские потоки

- ADR-2024-06-09 фиксирует стратегию интеграции прототипа Avokey/EvoNeuronCore как исследовательской возможности внутри контуров Context Engine. См. `docs/adr/ADR-20240609-avokey-evoneuroncore-integration.md` для деталей о фичефлагах и границах безопасности.
