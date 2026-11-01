# arch-standards-check

Автоматическая проверка применимости архитектурных стандартов
к proposal через локальный **Nimble 9B** (`http://localhost:11434/v1/systemone`)
и агрегация решения «нужен ли корпоративный архитектор».

Версия: **MVP 0.1** (2026-10-04)

## Структура проекта

````
arch-standards-check/
├── README.md
├── requirements.txt
├── standards/
│   ├── reliability/
│   │   └── v2.0.yaml
│   └── monitoring/
│       └── v2.1.yaml
├── tools/
│   ├── __init__.py
│   └── nimble_applicability.py
├── tests/
│   └── fixtures/
│       ├── proposal-wallet-fl.md
│       ├── proposal-ui-fix.md
│       └── proposal-monitoring.md
└── scripts/
    ├── run-reliability.sh
    ├── run-monitoring.sh
    └── smoke-test.sh
````

Автоматическая проверка применимости архитектурных стандартов к proposal
через локальный Nimble 9B (`http://localhost:11434/v1/systemone`).

# Что делает

Для каждого предложения (proposal в терминах OpenSpec) инструмент:

1. Читает 7 архитектурных стандартов из `standards/`.
2. Быстро отсеивает заведомо неприменимые стандарты через `precheck_keywords`.
3. Для оставшихся — задаёт Nimble по каждому требованию один вопрос:
   > Применимо ли это требование к описанному proposal?
4. Собирает вердикт: `applicable` / `not_applicable` / `unclear`.
5. Агрегирует глобальный вердикт:
   - **`architect_required`** — хотя бы одно требование применимо
   - **`architect_not_required`** — ни одно требование не применимо
   - **`escalate`** — есть требования с неясным ответом

Результат пишется в JSON-отчёт (`architect-involvement.json`)
и может быть приложен к change как артефакт аудита.

## Как это работает
proposal.md
    │
    ▼
┌──────────────────────────────────┐
│ precheck по ключевым словам      │
│ (стандарт скипается, если        │
│  ни одного ключа нет)            │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│ Nimble: применимо ли требование? │
│ (для каждого требования)         │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│ decision_from():                 │
│   conf >= 0.80 OR margin >= 0.20 │
│   → принимаем choice             │
│   иначе → unclear                │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│ агрегация по всем стандартам     │
│ → architect_required /           │
│   architect_not_required /       │
│   escalate                       │
└──────────────────────────────────┘
    │
    ▼
architect-involvement.json

---

## Зачем

Корпоративный архитектор нужен не для каждого изменения.
Тривиальные правки (тексты, лейблы, косметика) не должны его отвлекать.
Но и пропустить архитектурно значимое изменение нельзя.

Инструмент даёт **воспроизводимое, объяснимое и аудируемое** решение —
на базе формальных критериев применимости, зафиксированных в стандартах.

---

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Проверка Nimble

Убедиться, что Nimble отвечает:

```bash
curl -s http://localhost:11434/v1/systemone -d '{
  "model": "nimble",
  "state": "тест",
  "questions": {"label": {"type": "choice",
    "instructions": "тест",
    "criteria": {"да": null, "нет": null}}}
}' | head -c 300
```

## Запуск

```bash
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --output /tmp/reliability-report.json
```

## Отладка

Первый вызов с `--raw` печатает сырой ответ Nimble и выходит:

```bash
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --raw
```

## Пороги

- `--trust 0.80` — выше — принимаем решение Nimble как есть
- `--gray 0.55` — ниже — сразу `unclear`

Между 0.55 и 0.80 — серая зона, тоже `unclear`, но помечается флагом `gray_zone`.

## Exit codes

- `0` — ок
- `1` — HTTP / connection error
- `2` — input error
- `3` — timeout