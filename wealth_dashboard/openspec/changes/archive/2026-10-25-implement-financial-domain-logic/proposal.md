---
name: Implement Financial Domain Logic
description: Implement behavioral requirements for valuation_date staleness, ValuationHistory recording, and FinancialGoal progress tracking
type: project
category: code_standard
keywords:
  - "financial domain logic"
  - "staleness check"
  - "valuation history recording"
  - "goal progress"
  - "wealth dashboard"
usage_scenarios:
  - "Implementing behavioral logic for financial data models"
  - "Adding staleness warnings to asset tracking"
  - "Implementing automatic valuation history recording"
---

# Proposal

## Why

The `define-financial-domain-schema` change creates the tables and columns but implements zero spec scenarios. The spec defines 14 behavioral scenarios across staleness warnings, valuation history recording, and goal progress — none of which work with schema alone. Without this change, the user gets empty tables with no functional value.

This change implements the behavioral layer on top of the schema foundation.

## What Changes

- Add `is_stale` property to `Asset` and `Liability` models (90-day threshold)
- Add `get_stale_records(session)` helper to surface stale records in the dashboard
- Add `record_valuation_change()` method to `Asset` and `Liability` models
- Add SQLAlchemy `before_update` event to auto-capture `ValuationHistory` on value changes
- Add `current_value` column and `progress_percentage` property to `FinancialGoal`
- Add `effective_currency` property to all financial models (returns 'RUB' when `currency` is `None`)

## Capabilities

### New Capabilities
- `local-persistence`: Staleness warnings, automatic valuation history recording, goal progress tracking

## Impact

- `models.py`: Add properties and methods to existing models
- `main.py`: Wire `get_stale_records()` into dashboard view
- `metrics.py`: Use `effective_currency` instead of raw `currency` for currency-grouped calculations
- All downstream code must handle nullable `valuation_date` (treat as stale)

## Dependencies

- **Requires** `define-financial-domain-schema` to be applied first (tables and columns must exist)
- No UI changes in this change — stale records and goal progress are exposed via API endpoints for Phase 4 UI work
