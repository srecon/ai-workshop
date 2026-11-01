#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PROPOSAL="${1:-tests/fixtures/proposal-wallet-fl.md}"
OUT="${2:-/tmp/reliability-report.json}"

python3 tools/nimble_applicability.py \
  --proposal "$PROPOSAL" \
  --standard standards/reliability/v2.0.yaml \
  --output "$OUT"