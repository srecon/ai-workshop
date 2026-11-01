---
name: architect-involvement
description: Проверяет, нужен ли корпоративный архитектор для proposal (OpenSpec change) по архитектурным стандартам через Nimble 9B.
color: Green
---

# Architect Involvement

Роль: оркестрация проверки. Логика — в `tools/architect_involvement.py`, не дублируй её.

## Триггер

Пользователь просит проверить proposal на архитектурную значимость,
или в репо появился новый `changes/<id>/proposal.md`.

## Вызов

```bash
python3 tools/architect_involvement.py \
  --proposal changes/<id>/proposal.md \
  --standards-dir standards/ \
  --output changes/<id>/architect-involvement.json

```
Никогда не вызывай Nimble напрямую. Никогда не интерпретируй stdout.
Решение — только поле decision в JSON.

## Exit codes

Код	Действие
0	Читать JSON, сформировать отчёт
1	Nimble недоступен — остановиться, сообщить пользователю
2	Ошибка входных данных — показать stderr, остановиться
3	Timeout — предложить --timeout 300

## Решение
decision	Что делать
architect_required	Уведомить: нужен архитектор. Показать triggered_standards
architect_not_required	Уведомить: архитектор не требуется
escalate	Уведомить: нужна ручная проверка. Показать unclear-требования
Не подменяй decision собственным выводом.

## Формат отчёта

Используй поле `rationale` из JSON как основу. Отчёт делится
на два блока: **что проверено** и **что пропущено**.

```markdown
## Проверка архитектурной значимости

**Proposal:** `changes/<id>/proposal.md`
**Решение:** `<decision>`

**Обоснование:** <rationale из JSON>

### Проверено через Nimble

| Стандарт | Версия | applicable | not_applicable | unclear |
|----------|--------|-----------|----------------|---------|
| reliability | 2.0 | 0 | 6 | 0 |

### Пропущено по precheck

`ai_ml`, `db_design`, `gateways`, `integrations`, `monitoring`, `platform_ready`
— нет сигналов в proposal.

### Требования, требующие внимания

(показывать только если есть applicable или unclear)

- `<code>` (<standard>) — <verdict>, conf=<X>

### Артефакт

`changes/<id>/architect-involvement.json`
```

**Правила:**
- Если `decision = architect_not_required` и блок «Проверено» не пуст —
  обязательно показать его. Это доказательство, что проверка была.
- Блок «Пропущено» оставлять всегда — он объясняет, почему проверка
  заняла мало времени.
- Блок «Требования» показывать только если есть `applicable` или `unclear`.

## Политика
Не делай повторных вызовов без причины.

Не редактируй architect-involvement.json вручную.

Не выдумывай требования, которых нет в JSON.

````
# Как сохранить

У меня нет возможности прикрепить файл в этом интерфейсе, но вот два способа:

### Способ 1: вручную

```bash
mkdir -p skills
# скопируй блок выше в файл skills/architect-involvement.md
````