# Remediation Plan

Project: {{project}}
Based on: {{date}}

{{#each actions}}
## {{index}}. {{area}}

Problem:
{{problem}}

Action:
{{action}}

Components:
{{#each components}}
- {{this}}
{{/each}}

Files affected:
{{#each files}}
- {{this}}
{{/each}}

{{/each}}

## Approval

⚠️ Apply changes? (yes / no / selective)
