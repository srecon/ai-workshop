# Design

## Context

The `define-financial-domain-schema` change creates the following tables and columns:

- `assets`: `valuation_date` (DateTime, nullable), `currency` (String, default 'RUB')
- `liabilities`: `valuation_date` (DateTime, nullable), `currency` (String, default 'RUB')
- `income`: `currency` (String, default 'RUB')
- `expenses`: `currency` (String, default 'RUB')
- `valuation_history`: `id`, `asset_id` (FK, nullable, ON DELETE SET NULL), `liability_id` (FK, nullable, ON DELETE SET NULL), `field_name`, `old_value` (DECIMAL), `new_value` (DECIMAL), `changed_at`, `change_reason`
- `financial_goals`: `id`, `name`, `target_amount` (DECIMAL), `target_date`, `currency`, `description`, `notes`, `current_value` (DECIMAL)

This change implements the behavioral layer on top of that schema.

## Goals / Non-Goals

**Goals:**
- Implement `is_stale` property on `Asset` and `Liability` (90-day threshold)
- Implement `get_stale_records(session)` helper
- Implement `record_valuation_change()` method on `Asset` and `Liability`
- Implement SQLAlchemy `before_update` event to auto-capture `ValuationHistory`
- Implement `progress_percentage` property on `FinancialGoal`
- Implement `effective_currency` property on all financial models

**Non-Goals:**
- No UI changes (Phase 4)
- No currency conversion logic (Phase 6)
- No import preview or validation (Phase 2)
- No CRUD endpoints (Phase 3)
- No export/backup (Phase 5)

## Decisions

### Decision 1: `is_stale` as a computed property, not a column

The `is_stale` check compares `valuation_date` against `datetime.utcnow()` minus 90 days. This is computed on every access, not stored.

**Why:** Staleness is a function of time, not a fixed attribute. A record that is stale today may be fresh tomorrow (if the user updates it). Storing a flag would require recomputing it on every access or running a background job — both add complexity for negligible performance gain at this scale (< 10,000 records).

**Trade-off:**
- **Pro:** Always accurate, no storage, no sync issues
- **Con:** Computed on every access — negligible for < 10,000 records, but would need an index on `valuation_date` at scale

### Decision 2: `before_update` SQLAlchemy event for automatic history recording

Instead of requiring every controller or service to manually call `record_valuation_change()`, we register a SQLAlchemy `@event.listens_for(Asset, 'before_update')` that automatically creates a `ValuationHistory` record when `current_value` or `purchase_price` changes.

**Why:** Manual calls are error-prone. A developer could update `asset.current_value` without calling the recording method, and the history would be silently lost. An event listener is transparent and guaranteed to fire.

**Trade-off:**
- **Pro:** Guaranteed history capture, no API surface to forget
- **Con:** Hidden behavior — a developer reading the code won't see an explicit `ValuationHistory` creation call; they need to know about the event listener. This is a "magic" behavior that should be documented.

### Decision 3: `ON DELETE SET NULL` for `ValuationHistory` foreign keys

When an asset or liability is deleted, its history records remain but the reference is cleared.

**Why:** Preserves the audit trail (you can still see that a value changed, when, and by how much) without creating broken references. The alternative — `ON DELETE CASCADE` — loses the audit trail entirely. `ON DELETE RESTRICT` (SQLite default) blocks deletion, creating a poor UX.

**Trade-off:**
- **Pro:** Audit trail preserved, deletes work cleanly
- **Con:** After deletion, you lose the ability to tell which specific asset a history record belonged to — but you still have the `changed_at` timestamp and value changes

### Decision 4: `current_value` on `FinancialGoal` is a manual field, not computed

The `FinancialGoal` model gets a `current_value` column (DECIMAL) that the user updates manually. Progress is calculated as `(current_value / target_amount) * 100`.

**Why:** Automatic progress calculation requires a junction table (`goal_assets`) linking goals to assets, which adds complexity and a new table. This belongs in a dedicated "Financial Goals Implementation" change in Phase 4. For this change, manual tracking is sufficient — the user can manually set "I have 350,000 RUB saved for my emergency fund."

**Trade-off:**
- **Pro:** Simple, works for manual goal tracking, no schema changes beyond one column
- **Con:** Requires manual updates — the user must remember to update `current_value` as their portfolio changes
- **Alternative:** Junction table `goal_assets` with automatic progress calculation — more powerful, but out of scope for this change

### Decision 5: `effective_currency` property returns 'RUB' when `currency` is `None`

All financial models get an `effective_currency` property that returns `'RUB'` when the raw `currency` column is `None`.

**Why:** Pre-migration data imported before this change has `currency = NULL` (the column didn't exist). SQLite returns `None` for that column. Without the property, downstream code treating `None` as "unknown currency" would exclude existing records from RUB totals, breaking backward compatibility.

**Trade-off:**
- **Pro:** Transparent handling of pre-migration data, no migration script needed for correctness
- **Con:** Hides the fact that the column is NULL — a developer inspecting the raw column would see `None`, not `'RUB'`. The property is the source of truth, but raw column reads are misleading.
