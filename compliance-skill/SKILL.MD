---
name: platform-ready-compliance
version: 2.8.0
description: Проверка Java-проектов на соответствие стандарту Platform-Ready 5.3.1. SKILL.MD является исполнителем и оркестратором. Детальная логика проверок находится в rules/*.yaml, а корпоративные компоненты — в corporate-components/*.yaml. Skill автоматически сопоставляет требования стандарта с Rule Registry, выполняет проверки по Rule-файлам, собирает evidence и формирует воспроизводимый compliance report.
allowed-tools: Glob, Grep, Read, Bash(git status:*), Bash(git log:*), Bash(find:*), Bash(wc:*), Write
trigger-keywords:
  - platform-ready
  - platform ready
  - TSCPR
  - compliance
  - compliance review
  - проверка соответствия
  - platform ready compliance
---

# Platform-Ready Compliance — ИНСТРУКЦИЯ К ИСПОЛНЕНИЮ

## 1. РОЛЬ SKILL.MD

Ты — агент Qwen Code CLI.

`SKILL.MD` — **оркестратор и исполнитель**, но не источник детальной логики конкретных compliance-проверок.

Архитектура Skill:

```text
Platform-Ready Standard
        ↓
requirements/platform_ready_5.3.1.md
        ↓
rules/registry.yaml
        ↓
rules/PR-*.yaml
        ↓
corporate-components/*.yaml
        ↓
Project Evidence
        ↓
Compliance Result
```

Используй следующие принципы:

```text
SKILL.MD
= HOW TO EXECUTE

Rule YAML
= WHAT TO CHECK

Corporate Component
= WHICH APPROVED COMPONENT / IMPLEMENTATION

Project
= EVIDENCE

Report
= RESULT
```

**Не дублируй patterns, dependency coordinates, detection logic или result rules из Rule YAML внутри `SKILL.MD`.**

---

# 2. ОСНОВНОЙ ИСТОЧНИК ИСТИНЫ

Для каждой конкретной проверки единственным источником логики является соответствующий Rule-файл из `rules/`.

Не используй старую или запомненную логику из предыдущих версий Skill.

Если Rule-файл изменился, используй новую версию без изменения `SKILL.MD`.

Если Rule YAML отсутствует или невалиден:

```text
STATUS = MANUAL_REVIEW
CONFIDENCE = LOW
REASON = "Rule file missing or invalid"
```

Не создавай fallback-логику, которой нет в Rule-файле.

---

# 3. СТРУКТУРА SKILL

Ожидаемая структура:

```text
platform-ready-compliance/
│
├── SKILL.MD
│
├── requirements/
│   └── platform_ready_5.3.1.md
│
├── rules/
│   ├── registry.yaml
│   ├── PR-*.yaml
│   └── ...
│
├── corporate-components/
│   ├── catalog.yaml
│   └── *.yaml
│
└── templates/
    ├── report.md.tpl
    └── remediation.md.tpl
```

---

# 4. АКТИВАЦИЯ

Если пользователь просит:

- `platform-ready compliance`
- `проверь Platform-Ready`
- `сделай compliance review`
- `проверь TSCPR_...`
- `проверь проект на соответствие стандарту`

→ немедленно начинай выполнение.

Дополнительный вопрос допустим только тогда, когда невозможно определить корень проекта автоматически.

---

# 5. АЛГОРИТМ ВЫПОЛНЕНИЯ

## ШАГ 1. Определи корень проекта

Используй `Glob` для поиска:

```text
**/pom.xml
**/build.gradle
**/build.gradle.kts
**/settings.gradle
**/settings.gradle.kts
```

Определи:

```text
PROJECT_ROOT
PROJECT_TYPE
```

Если найдено несколько build-файлов, считай проект multi-module и анализируй соответствующие модули.

Не анализируй generated directories (`target`, `build`, `.gradle`, `.git` и т.п.), если они не указаны конкретным Rule-файлом как источник evidence.

---

## ШАГ 2. Загрузи стандарт

Прочитай:

```text
requirements/platform_ready_5.3.1.md
```

Используй этот файл для определения:

- списка требований;
- `TSCPR_*` ID;
- официальной формулировки требования;
- области применимости;
- указанного стандартом способа проверки (`Автоматизированный`, `Ручной` и т.п.).

**Не заменяй формулировку требования собственной формулировкой.**

---

## ШАГ 3. Загрузи Rule Registry

Прочитай:

```text
rules/registry.yaml
```

Registry определяет:

- какие требования покрываются Skill;
- `rule_id`;
- путь к Rule YAML;
- включено ли правило (`enabled`).

Не хардкодь список Rule ID в `SKILL.MD`.

---

## ШАГ 4. Проверь целостность Registry

Для каждого включённого правила из Registry:

1. Проверь, что Rule-файл существует.
2. Прочитай его через `Read`.
3. Проверь, что YAML имеет корректный синтаксис и единый Rule Contract.
4. Проверь совпадение:

```text
registry.requirement
        ==
rule.requirement
```

Если совпадения нет:

```text
STATUS = MANUAL_REVIEW
CONFIDENCE = LOW
REASON = "Registry and Rule requirement mismatch"
```

Не исправляй Registry или Rule во время обычного review.

---

# 6. ВЫБОР ПРОВЕРОК

## Полный review

Если пользователь просит полный compliance review:

```text
выполни все enabled rules из rules/registry.yaml
```

## Проверка конкретного требования

Если пользователь указал `TSCPR_*`:

1. Найди его в Registry.
2. Определи соответствующий Rule.
3. Выполни только этот Rule.

Если requirement отсутствует в Registry:

```text
STATUS = NOT_COVERED
```

Не придумывай Rule для отсутствующего requirement.

---

# 7. RULE CONTRACT

Каждый Rule YAML должен интерпретироваться по единому контракту.

Обязательные концептуальные поля:

```yaml
schema_version:
rule_id:
name:
requirement:
standard_source:
scope:
checks:
decisions:
```

Необязательные поля:

```yaml
components:
approved_schemes:
derived_flags:
interpretation:
follow_references:
recommendation:
execution_notes:
```

### `checks`

Каждый check содержит:

```yaml
id:
purpose:
sources:
```

Каждый `source` обычно содержит:

```yaml
glob:
patterns:
```

Rule может использовать специализированные поля:

```yaml
type: maven_dependency
dependencies:
  - groupId:
    artifactId:
exclude_globs:
unknown_if_no_source:
correlation_group:
```

`type: maven_dependency` означает, что агент должен разобрать реальные `<dependency>` блоки POM и сопоставить `groupId` + `artifactId`, а не искать две строки независимо. Evidence должен указывать `pom.xml:<line>`.

`exclude_globs` запрещает использовать соответствующие файлы как production evidence конкретной проверки.

`unknown_if_no_source: true` означает: если источник нельзя найти в repository, результат check должен быть `UNKNOWN`, а не `NOT_DETECTED`.

`correlation_group` используется для архитектурных цепочек. Evidence нескольких checks одной группы должно быть связано с одним workload/pipeline и не может быть случайным совпадением из разных компонентов проекта.

Дополнительные поля могут использоваться Rule-файлом, если их смысл однозначен из структуры Rule.

### `decisions`

`decisions` определяют итоговый статус.

Условия могут использовать:

```text
check
all
any
derived
```

Исполняй `decisions` **в порядке, указанном Rule-файлом**.

Первое применимое условие определяет итоговый результат.

---

# 8. ИСПОЛНЕНИЕ CHECKS

Для каждого Rule:

1. Прочитай `checks`.
2. Для каждого `source.glob` найди файлы через `Glob`.
3. Если `source.type == maven_dependency`, разберите `<dependency>` блоки найденных POM и сопоставьте точные `groupId` + `artifactId`.
4. Иначе для каждого `pattern` выполни `Grep`.
5. Примени `exclude_globs`, если они указаны.
6. Для каждого существенного совпадения зафиксируй `file:line`.
7. При необходимости прочитай контекст через `Read`.
8. Если `unknown_if_no_source: true` и source files недоступны, установи `UNKNOWN`.
9. Если проверяемая конструкция найдена, установи `DETECTED`; если все доступные источники проверены и evidence нет — `NOT_DETECTED`.
10. Определи состояние check.

Допустимые состояния:

```text
DETECTED
NOT_DETECTED
UNKNOWN
NOT_APPLICABLE
```

Используй состояния и специальные оговорки, определённые конкретным Rule.

---

# 9. ПРАВИЛО CONTEXT VALIDATION

`Grep`-совпадение само по себе не всегда означает compliance evidence.

Если pattern потенциально неоднозначен, после `Grep` обязательно прочитай контекст через `Read`.

Особенно это относится к:

- generic class names;
- generic configuration keys;
- инфраструктурным images;
- словам `kafka`, `compliance`, `aml`, `logging`, `istio`;
- аннотациям Kubernetes;
- shared ConfigMaps;
- Maven dependency patterns.

Не превращай слабый keyword match в архитектурный факт.

---

# 10. UNKNOWN И MISSING

Различай:

```text
NOT_DETECTED
```

и

```text
UNKNOWN
```

`NOT_DETECTED` означает, что доступные источники были проверены и evidence не найден.

`UNKNOWN` означает, что источник недоступен, scope находится вне repository или evidence нельзя подтвердить.

Например:

```text
Deployment отсутствует в repository
```

не всегда означает:

```text
Deployment отсутствует вообще
```

Возможны:

- отдельный infrastructure repository;
- внешний Helm chart;
- platform-managed deployment;
- runtime injection;
- configuration вне текущего проекта.

---

# 11. CORPORATE COMPONENTS

Если Rule содержит:

```yaml
components:
  - component-id
```

прочитай соответствующий компонент из:

```text
corporate-components/catalog.yaml
```

и затем соответствующий component YAML.

Corporate Component определяет:

- название компонента;
- известные Maven coordinates;
- допустимые способы использования;
- capabilities;
- известные deployment signals.

**Corporate Component не определяет compliance verdict.**

Compliance verdict определяется только Rule YAML.

Наличие dependency компонента является evidence наличия компонента, но не автоматически означает compliance, если Rule требует фактическое использование или deployment integration.

---

# 12. DEPENDENCY ANALYSIS

Для Maven:

1. Прочитай `pom.xml` всех релевантных модулей.
2. Извлеки:
   - `groupId`;
   - `artifactId`;
   - `version`;
   - `scope`.
3. Учитывай Maven properties.
4. Сопоставляй dependency только с компонентами/паттернами из Rule или Corporate Component Catalog.

Не придумывай Maven coordinates.

Не используй зависимость как автоматический `PASS`, если Rule этого не требует.

---

# 13. JAVA ANALYSIS

Для Java используй:

```text
Glob: **/src/main/java/**/*.java
```

а для тестов отдельно:

```text
Glob: **/src/test/java/**/*.java
```

Не смешивай production и test evidence, если Rule их различает.

Каждый существенный match должен содержать:

```text
<file>:<line>
```

---

# 14. CONFIGURATION / KUBERNETES ANALYSIS

Для deployment/configuration анализируй только источники, предусмотренные Rule.

Типичные источники:

```text
application*.yml
application*.yaml
application*.properties
k8s/**/*.yaml
k8s/**/*.yml
helm/**/*.yaml
helm/**/*.yml
openshift/**/*.yaml
openshift/**/*.yml
Dockerfile*
Containerfile*
```

Не считай наличие любого Kubernetes или Docker-файла доказательством конкретного compliance requirement.

---

# 15. DERIVED FLAGS

Если Rule содержит `derived_flags`, вычисли их после выполнения базовых checks.

Например:

```text
synapse_active
ott_4g_ready
mtls_ready
```

Derived flag не является новым evidence.

Он только объединяет результаты базовых checks согласно definition конкретного Rule.

Не придумывай собственную формулу derived flag.

---

# 16. DECISION ENGINE

После выполнения всех checks:

1. Вычисли derived flags. Derived flag может иметь значение `TRUE`, `FALSE` или `UNKNOWN`, если Rule это определяет.
2. Для условий `all` все дочерние условия должны выполняться. Для `any` достаточно одного.
3. Пройди `decisions` по порядку.
4. Найди первое применимое условие.
5. Возьми из него:
   - `status`;
   - `confidence`;
   - `reason`.

Допустимые итоговые статусы:

```text
PASS
ERROR
MANUAL_REVIEW
N/A
NOT_COVERED
```

Не создавай собственные альтернативные статусы.

---

# 17. НЕЛЬЗЯ ВЫДАВАТЬ PASS БЕЗ ДОКАЗАТЕЛЬСТВА

Для `PASS` должны существовать конкретные evidence, которые удовлетворяют условию `decisions` соответствующего Rule.

Нельзя писать:

```text
PASS because project looks compliant
```

Нужно писать:

```text
PASS

Evidence:
- file:line — concrete evidence
```

---

# 18. TRACEABILITY

Каждый результат должен иметь цепочку:

```text
Platform-Ready Requirement
        ↓
Rule ID
        ↓
Check
        ↓
Evidence
        ↓
Decision
        ↓
Status
        ↓
Recommendation
```

Если выполнялось remediation:

```text
        ↓
Fix
        ↓
Re-check
        ↓
New Result
```

---

# 19. SPECIAL CASE: MANUAL REQUIREMENTS

Если стандарт прямо указывает, что проверка является ручной:

```text
Rule MAY collect automatic evidence
```

но не должен автоматически превращать неполное evidence в `PASS`.

В этом случае Rule может завершаться:

```text
MANUAL_REVIEW
```

с перечнем того, что требуется проверить архитектору.

---

# 20. REPORT

Используй `templates/report.md.tpl`, если он применим.

Отчёт должен содержать:

```text
Project
Standard
Skill version
Mode
Date
Git commit

Summary

Findings

Manual Review

Not Covered
```

Для каждого finding показывай:

```text
Requirement
Rule
Status
Confidence
Requirement text
Evidence
Finding / Reason
Recommendation
```

---

# 21. COVERAGE REPORT

После полного review автоматически сравни:

```text
requirements/platform_ready_5.3.1.md
```

с:

```text
rules/registry.yaml
```

Каждое требование из стандарта должно попасть в одну категорию:

```text
COVERED
NOT_COVERED
```

`COVERED` означает наличие enabled Rule в Registry.

`NOT_COVERED` означает отсутствие Rule в Registry.

Не считай наличие Corporate Component покрытием requirement.

Не считай наличие документа с названием требования покрытием requirement.

---

# 22. CURRENT COVERAGE

Текущий архив содержит только существующие правила проекта.

Не добавляй новые requirements или compliance rules автоматически.

Все требования, которых нет в Registry, должны оставаться `NOT_COVERED` до тех пор, пока пользователь отдельно не добавит Rule.

---

# 23. REMEDIATION

Обычный compliance review — **read-only**.

Не изменяй проект автоматически.

Если пользователь явно просит исправить найденные ошибки:

1. Используй recommendation из Rule.
2. Определи затрагиваемые файлы.
3. Не придумывай корпоративные API.
4. Не заменяй корпоративную библиотеку самодельной реализацией без указания пользователя.
5. После изменения снова выполни исходный Rule.
6. Покажи BEFORE / CHANGES / AFTER.

---

# 24. НЕ СОЗДАВАТЬ НОВУЮ ЛОГИКУ В SKILL.MD

Запрещено добавлять в `SKILL.MD` конкретные requirement-specific `IF/THEN` условия, dependency patterns, technology patterns или detection heuristics.

Такая логика должна находиться в соответствующем Rule YAML.

Такая логика должна находиться в соответствующем Rule YAML.

`SKILL.MD` может описывать только общий execution framework.

---

# 25. НЕ ПОДМЕНЯТЬ RULE CATALOG

Не использовать:

```text
corporate-components/*.yaml
```

как самостоятельный источник compliance verdict.

Compliance verdict берётся из:

```text
rules/*.yaml
```

Corporate Components используются для сопоставления approved implementation и evidence.

---

# 26. НЕ ИЗОБРЕТАТЬ КОРПОРАТИВНЫЕ КОМПОНЕНТЫ

Если Rule требует approved component, но компонент не описан в Catalog:

```text
MANUAL_REVIEW
```

Не придумывай:

- Maven coordinates;
- package names;
- class names;
- API methods;
- configuration keys;
- endpoints;
- Kafka brokers;
- Kafka topics;
- Kubernetes Secrets.

---

# 27. GIT КОНТЕКСТ

Перед remediation, если необходимо, используй:

```text
Bash(git status:*)
Bash(git log:*)
```

Не удаляй и не перезаписывай незакоммиченные пользовательские изменения.

---

# 28. ИТОГОВАЯ МОДЕЛЬ

```text
                         ┌─────────────────────────┐
                         │ Platform-Ready 5.3.1   │
                         │ requirements/*.md      │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      Rule Registry      │
                         │      rules/registry     │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
          ┌─────────────────────┐             ┌────────────────────┐
          │   Compliance Rules  │             │ Corporate Catalog  │
          │     rules/*.yaml    │             │ corporate-components│
          └──────────┬──────────┘             └─────────┬──────────┘
                     │                                  │
                     └──────────────┬───────────────────┘
                                    ▼
                         ┌─────────────────────────┐
                         │    Rule Executor       │
                         │       SKILL.MD         │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Project Evidence    │
                         │ Java / Maven / SQL      │
                         │ Config / K8s / Helm      │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │   Compliance Report     │
                         │ PASS / ERROR / MANUAL   │
                         │ N/A / NOT_COVERED       │
                         └─────────────────────────┘
```

Главный принцип:

```text
SKILL.MD не должен знать,
как конкретно проверяется Logging, Persistence, OTT и т.д.

SKILL.MD должен знать только,
как загрузить Rule и как его исполнить.
```
