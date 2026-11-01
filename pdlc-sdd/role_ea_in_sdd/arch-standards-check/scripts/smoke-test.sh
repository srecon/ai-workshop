#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "==> 1. Проверка Nimble"
curl -s http://localhost:11434/v1/systemone -d '{
  "model": "nimble",
  "state": "тест",
  "questions": {"label": {"type": "choice",
    "instructions": "тест",
    "criteria": {"да": null, "нет": null}}}
}' | head -c 300
echo

echo "==> 2. Сырой ответ Nimble (первое требование reliability)"
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --raw

echo "==> 3. Reliability × wallet-fl (ожидание: architect_required)"
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-wallet-fl.md \
  --standard standards/reliability/v2.0.yaml \
  --output /tmp/reliability-wallet.json

echo "==> 4. Reliability × ui-fix (ожидание: architect_not_required)"
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-ui-fix.md \
  --standard standards/reliability/v2.0.yaml \
  --output /tmp/reliability-ui.json

echo "==> 5. Monitoring × monitoring (ожидание: architect_required)"
python3 tools/nimble_applicability.py \
  --proposal tests/fixtures/proposal-monitoring.md \
  --standard standards/monitoring/v2.1.yaml \
  --output /tmp/monitoring-mon.json

echo "==> Готово. Отчёты в /tmp/"