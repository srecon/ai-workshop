# Compliance Rules

Each `PR-*.yaml` is an executable compliance rule definition mapped to exactly one Platform-Ready requirement in `registry.yaml`.

`SKILL.MD` must execute these files and must not contain requirement-specific patterns or decision logic.

Rule YAMLs use a common contract: `schema_version`, `rule_id`, `name`, `requirement`, `standard_source`, `scope`, `checks`, `decisions`, with optional `components`, `derived_flags`, `interpretation`, `follow_references`, and `recommendation`.
