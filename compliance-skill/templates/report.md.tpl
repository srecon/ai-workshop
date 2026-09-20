# Platform-Ready Compliance Report

Project: {{project}}
Standard: Platform-Ready 5.3.1
Skill version: 2.8.0
Mode: {{mode}}
Date: {{date}}
Git commit: {{commit}}

## Summary

| Rule | Area | Requirement | Result | Confidence |
|---|---|---|---|---|
{{#each summary}}
| {{rule}} | {{area}} | {{requirement}} | {{result}} | {{confidence}} |
{{/each}}

## Findings

{{#each findings}}
### {{requirement}}

Status: {{status}}
Confidence: {{confidence}}

Requirement:
{{requirementText}}

Evidence:
{{#each evidence}}
- {{file}}:{{line}} — {{snippet}}
{{/each}}

Detected:
{{detected}}

Recommendation:
{{recommendation}}

---
{{/each}}

## Not covered by Skill v2.8.0

| Requirement | Status |
|---|---|
{{#each notCovered}}
| {{requirement}} | {{status}} |
{{/each}}
