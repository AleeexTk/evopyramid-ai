# EvoMethod_SK Integration Guide

## Архитектура Двойной Памяти

**EvoMethod_SK №1 - Перенаправление Хаоса**
- Для легких сессий и быстрых ответов
- Эфемерные сниппеты, мобильная пирамида
- Низкая задержка (< 100мс)

**EvoMethod_SK №2 - Фундаментальная Память Хаоса**
- Для сложных проектов и архитектур
- Золотые/Платиновые состояния блоков
- Четверная обработка (QAP)

## Быстрый старт

```python
from apps.core.intent.collective_mind import EvoCollectiveMind

mind = EvoCollectiveMind()
result = await mind.process_intent("Ваш запрос", контекст)
```

## Мониторинг Памяти

```bash
# Запуск EvoCodex проверок
python3 -m compileall apps/core/integration/evo_archaic_gateway.py

# Тестирование анализатора структуры
cd apps/core/analysis && python3 json_structure_analyzer.py
```

## Цветовая Кодировка Памяти

- 🟨 Желтый: Базовые концепции
- 🟥 Красный: Конфликты и ошибки
- 🟩 Зеленый: Стратегии и решения
- 🟦 Синий: Данные и метрики
- 🟧 Оранжевый: Временные состояния
- 🏆 Золото: Высокая значимость
- ✨ Платина: Критическая важность
