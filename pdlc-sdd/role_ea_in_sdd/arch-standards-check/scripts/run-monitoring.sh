#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PROPOSAL="${1:-tests/fixtures/proposal-monitoring.md}"
OUT="${2:-/tmp/monitoring-report.json}"

python3 tools/nimble_applicability.py \
  --proposal "$PROPOSAL" \
  --standard standards/monitoring/v2.1.yaml \
  --output "$OUT"