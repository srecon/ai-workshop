# Design

## Context

The current data model in `models.py` has five tables: `Asset`, `Liability`, `Income`, `Expense`, and `UserOverride`. Key gaps:

- `Asset` has `currency` but other models do not
- No `valuation_date` on any model — cannot track data freshness or historical trends
- No `ValuationHistory` table — cannot show net worth over time
- No `FinancialGoal` model — cannot track goals

## Goals / Non-Goals

**Goals:**
- Add `valuation_date` to `Asset` and `Liability` (nullable, defaults to today)
- Add `currency` to `Liability`, `Income`, `Expense` (nullable, defaults to 'RUB')
- Add `ValuationHistory` table to track value changes
- Add `FinancialGoal` model for future use
- Maintain backward compatibility — all new columns are nullable with defaults

**Non-Goals:**
- No currency conversion logic (Phase 6)
- No import preview or validation (Phase 2)
- No CRUD endpoints (Phase 3)
- No UI changes (Phase 4)
- No export/backup (Phase 5)

## Decisions

### Decision 1: Nullable columns with defaults

All new columns are nullable with sensible defaults (`valuation_date` defaults to today, `currency` defaults to 'RUB'). This ensures:
- Existing data is not broken
- The database migration is a simple `ALTER TABLE ... ADD COLUMN`
- Backward-compatible with existing parser output

### Decision 2: ValuationHistory as a separate table

Instead of embedding history in the main models, we create a separate `ValuationHistory` table with:
- `asset_id` or `liability_id` (nullable — points to either)
- `field_name` (e.g., 'current_value', 'purchase_price')
- `old_value`, `new_value`
- `changed_at` timestamp
- `change_reason` (nullable text)

This allows tracking changes to any field on any record without modifying the main models.

### Decision 3: FinancialGoal as a standalone model

The `FinancialGoal` model is created now but not wired to calculations yet. It will be used in Phase 4 (Financial Goals) for progress tracking. Fields:
- `name`, `target_amount`, `target_date`, `currency`, `description`, `notes`

### Decision 4: Database migration strategy

Since we're using SQLAlchemy with SQLite, we use `alembic` or manual migration:
- Add columns to existing tables (nullable)
- Create new tables (`valuation_history`, `financial_goals`)
- No data loss — existing records get default values
