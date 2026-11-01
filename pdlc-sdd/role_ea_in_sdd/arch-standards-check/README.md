# arch-standards-check
Automated check of applicability of architectural standards to a proposal via local Nimble 9B (http://localhost:11434/v1/systemone) and aggregation of the decision “is a corporate architect needed”.

Version: MVP 0.1 (2026-10-04)

## Project structure

```text
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
```
Automated check of applicability of architectural standards to a proposal via local Nimble 9B (http://localhost:11434/v1/systemone).

## What it does? 

For each proposal (in OpenSpec terms), the tool:

1. Reads 7 architectural standards from standards/ (Add your corporate standards in this directory).

2. Quickly filters out obviously inapplicable standards via precheck_keywords.

3. For the remaining ones, asks Nimble one question per requirement:

4. Is this requirement applicable to the described proposal?

5. Collects the verdict: applicable / not_applicable / unclear.

Aggregates the global verdict:

1. architect_required — at least one requirement is applicable

2. architect_not_required — no requirement is applicable

3. escalate — there are requirements with an unclear answer

The result is written to a JSON report (architect-involvement.json) and can be attached to the change as an audit artifact.

## How it works
```
proposal.md
│
▼
┌──────────────────────────────────┐
│ precheck by keywords │
│ (standard is skipped if │
│ no keywords are present) │
└──────────────────────────────────┘
│
▼
┌──────────────────────────────────┐
│ Nimble: is the requirement │
│ applicable? │
│ (for each requirement) │
└──────────────────────────────────┘
│
▼
┌──────────────────────────────────┐
│ decision_from(): │
│ conf >= 0.80 OR margin >= 0.20 │
│ → accept choice │
│ otherwise → unclear │
└──────────────────────────────────┘
│
▼
┌──────────────────────────────────┐
│ aggregation across all standards │
│ → architect_required / │
│ architect_not_required / │
│ escalate │
└──────────────────────────────────┘
│
▼
architect-involvement.json
```

## Why?
A corporate architect is not needed for every change.
Trivial edits (texts, labels, cosmetics) should not distract them.
But an architecturally significant change must not be missed.

The tool provides a reproducible, explainable, and auditable decision —
based on formal applicability criteria fixed in the standards.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Checking Nimble
Make sure Nimble responds:


curl -s http://localhost:11434/v1/systemone -d '{
  "model": "nimble",
  "state": "test",
  "questions": {"label": {"type": "choice",
    "instructions": "test",
    "criteria": {"yes": null, "no": null}}}
}' | head -c 300
Running

python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --output /tmp/reliability-report.json
Debugging
The first call with --raw prints the raw Nimble response and exits:


python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --raw
```

## Thresholds

--trust 0.80 — above — accept Nimble's decision as is

--gray 0.55 — below — immediately unclear

Between 0.55 and 0.80 is the gray zone, also unclear, but marked with the gray_zone flag.

## Exit codes

0 — ok

1 — HTTP / connection error

2 — input error

3 — timeout