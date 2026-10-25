---
name: Define Financial Domain
description: Establish canonical data model with valuation_date, ValuationHistory, and currency fields across all financial models
type: project
category: code_standard
keywords:
  - "financial domain model"
  - "valuation history"
  - "currency policy"
  - "data model foundation"
  - "wealth dashboard"
usage_scenarios:
  - "Defining canonical data model for financial applications"
  - "Adding valuation history to asset tracking"
  - "Establishing currency handling policy"
---

# Proposal

## Why

The current data model lacks `valuation_date` on all financial records, has no `ValuationHistory` table to track value changes over time, and hardcodes RUB as the currency on most models. Without these foundations, we cannot:

- Show historical net worth trends (FR-025)
- Track data freshness (FR-021)
- Support multi-currency portfolios (FR-026)
- Calculate accurate currency-converted totals (FR-027)

This change establishes the canonical data model that all subsequent changes depend on.

## What Changes

- Add `valuation_date` column to `Asset` and `Liability` models
- Add `currency` column to `Liability`, `Income`, and `Expense` models (already on `Asset`)
- Add new `ValuationHistory` table to track value changes over time
- Add `FinancialGoal` model for future goal-tracking capability
- Define currency policy: every financial value retains its original currency; conversion is optional and explicit

## Capabilities

### New Capabilities
- `local-persistence`: Enhanced with valuation history and financial goals

## Impact

- `models.py`: Add `valuation_date`, `currency` to existing models; add `ValuationHistory`, `FinancialGoal` models
- Database schema: New `valuation_history` table; existing tables get new columns
- All downstream code (parser, metrics, charts, main.py) must handle nullable `valuation_date`
