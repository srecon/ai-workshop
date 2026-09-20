# Platform-Ready Compliance

Skill для автоматизированной проверки Java-проектов на соответствие корпоративному стандарту Platform-Ready 5.3.1.

Skill анализирует код, зависимости, конфигурацию и deployment-артефакты проекта и формирует результат:

PASS — соответствие подтверждено;
ERROR — обнаружено нарушение;
MANUAL_REVIEW — автоматических доказательств недостаточно;
NOT_COVERED — для требования ещё нет правила.

## Архитектура

Проект разделён на четыре основных слоя:

```text
Platform-Ready Standard
        |
        v
Requirements
        |
        v
Rule Registry
        |
        +--------------------+
        |                    |
        v                    v
Compliance Rules      Corporate Components
        |                    |
        +---------+----------+
                  |
                  v
             Rule Executor
               SKILL.MD
                  |
                  v
            Project Evidence
                  |
                  v
          Compliance Report
```

Главная точка входа Skill.

Он отвечает за HOW:

- определение корня проекта;
- выбор правил;
- загрузку Rule-файлов;
- выполнение проверок;
- сбор Evidence;
- формирование отчёта.

Детальная логика конкретных требований не должна находиться в SKILL.md.

### requirements/

Содержит исходный корпоративный стандарт:

requirements/platform_ready_5.3.1.md

Это описание того, что требует стандарт.

### rules/

Содержит исполняемые правила compliance.

Каждое правило связано с одним требованием:

```text
Requirement
    ↓
Rule
    ↓
Checks
    ↓
Evidence
    ↓
Result
```

Каталог rules/registry.yaml связывает Requirement и Rule ID.

### corporate-components/

Содержит каталог корпоративных библиотек, сервисов и компонентов, которые могут использоваться при выполнении требований.

Важно:

Corporate Component не является автоматически Compliance Rule.

Например, StandIn может находиться в каталоге компонентов, но не является отдельным требованием Platform-Ready.


## Как добавить новое правило

Новые правила добавляются только для требований, существующих в Platform-Ready standard.

1. Найти требование

Открыть:

```requirements/platform_ready_5.3.1.md```

и определить:

- Requirement ID
- Requirement description

Например:

TSCPR_1-CC-02-05

2. Создать Rule-файл

Добавить файл:

```rules/PR-<NAME>-001.yaml```

Rule должен содержать единообразное описание:

```text
rule_id:
requirement:
name:
description:

scope:

checks:
  - ...

decision:
  - ...

evidence:
  - ...
```

recommendation:

Rule должен описывать:

- что проверять;
- где искать evidence;
- какие patterns использовать;
- когда результат PASS;
- когда ERROR;
- когда MANUAL_REVIEW.

3. Добавить правило в Registry

Изменить:

```rules/registry.yaml```

и связать:

```
Requirement
        ↓
Rule ID
        ↓
Rule file
```

4. Если нужны корпоративные компоненты

Не добавляй ```Maven dependencies``` непосредственно в ```SKILL.md```.

Добавь компонент в:

corporate-components/

и свяжи его с Rule.

5. Проверить правило

Проверить:

- YAML syntax;
- уникальность rule_id;
- корректность requirement;
- наличие Rule-файла;
- ссылки на corporate components;
- отсутствие противоречий между Rule и стандартом.

После этого Rule автоматически используется SKILL.md.

## Как запускать?

Перейти в корень анализируемого Java-проекта и запустить GigaCode CLI с подключённым Skill.

Полная проверка

```platform-ready compliance```

или:

```Проверь проект на соответствие Platform-Ready```

Skill определит проект и выполнит все доступные правила.

Проверка одного требования

Например:

```Проверь TSCPR_1-CC-02-05```

Skill загрузит соответствующий Rule и выполнит только эту проверку.

## Результат

Для каждого требования результат содержит:

- Requirement
- Rule
- Status
- Confidence
- Finding
- Evidence
- Recommendation

Главный принцип:

```text
Standard
   ↓
Requirement
   ↓
Rule
   ↓
Project Evidence
   ↓
Compliance Result

PASS нельзя выдавать без достаточного Evidence.
```

Если information недостаточно для автоматического вывода, используется MANUAL_REVIEW.
