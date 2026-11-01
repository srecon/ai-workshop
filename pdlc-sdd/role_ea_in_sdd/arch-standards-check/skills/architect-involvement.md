---
name: architect-involvement
description: Checks whether a corporate architect is needed for a proposal (OpenSpec change) according to architectural standards via Nimble 9B.
color: Green
---

# Architect Involvement

Role: orchestration of the check. The logic is in `tools/architect_involvement.py`; do not duplicate it.

## Trigger

The user asks to check a proposal for architectural significance,
or a new `changes/<id>/proposal.md` appears in the repo.

## Invocation

```bash
python3 tools/architect_involvement.py \
  --proposal changes/<id>/proposal.md \
  --standards-dir standards/ \
  --output changes/<id>/architect-involvement.json

```
Never call Nimble directly. Never interpret stdout.
The decision is only the `decision` field in the JSON.

## Exit codes

| Code | Action |
|------|--------|
| 0 | Read JSON, generate report |
| 1 | Nimble unavailable — stop, inform the user |
| 2 | Input data error — show stderr, stop |
| 3 | Timeout — suggest `--timeout 300` |

## Decision

| decision | What to do |
|----------|------------|
| architect_required | Notify: architect needed. Show `triggered_standards` |
| architect_not_required | Notify: architect not required |
| escalate | Notify: manual review needed. Show unclear requirements |

Do not substitute `decision` with your own conclusion.

## Report format

Use the `rationale` field from the JSON as the basis. The report is divided
into two blocks: **what was checked** and **what was skipped**.

```markdown
## Architectural significance check

**Proposal:** `changes/<id>/proposal.md`
**Decision:** `<decision>`

**Rationale:** <rationale from JSON>

### Checked via Nimble

| Standard | Version | applicable | not_applicable | unclear |
|----------|---------|------------|----------------|---------|
| reliability | 2.0 | 0 | 6 | 0 |

### Skipped by precheck

`ai_ml`, `db_design`, `gateways`, `integrations`, `monitoring`, `platform_ready`
— no signals in the proposal.

### Requirements requiring attention

(show only if there are applicable or unclear)

- `<code>` (<standard>) — <verdict>, conf=<X>

### Artifact

`changes/<id>/architect-involvement.json`
```

**Rules:**
- If `decision = architect_not_required` and the "Checked" block is not empty —
  be sure to show it. This is proof that the check was performed.
- Always leave the "Skipped" block — it explains why the check
  took little time.
- Show the "Requirements" block only if there are `applicable` or `unclear`.

## Policy
Do not make repeated calls without reason.

Do not edit architect-involvement.json manually.

Do not invent requirements that are not in the JSON.

````
# How to save

I cannot attach a file in this interface, but here are two ways:

### Method 1: manually

```bash
mkdir -p skills
# copy the block above into the file skills/architect-involvement.md
````