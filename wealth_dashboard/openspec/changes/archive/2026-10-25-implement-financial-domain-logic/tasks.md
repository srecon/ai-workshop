# Tasks

## 1. Add `is_stale` Property to Asset Model

- [ ] 1.1 Add `is_stale` property to `Asset` class — returns `True` if `valuation_date` is `None` or more than 90 days old — verify: `Asset.is_stale` returns correct boolean for NULL, old, and recent dates
- [ ] 1.2 Add `is_stale` property to `Liability` class — same logic as Asset — verify: `Liability.is_stale` returns correct boolean

## 2. Add `get_stale_records` Helper

- [ ] 2.1 Create `get_stale_records(session)` function in `metrics.py` or a new `stale_checker.py` — returns all stale assets and liabilities — verify: function returns correct list of stale records

## 3. Add `record_valuation_change` Method

- [ ] 3.1 Add `record_valuation_change(session, field_name, change_reason)` method to `Asset` class — creates a `ValuationHistory` record with `old_value`, `new_value`, `changed_at`, `change_reason` — verify: method creates history entry with correct values
- [ ] 3.2 Add `record_valuation_change(session, field_name, change_reason)` method to `Liability` class — same logic — verify: method creates history entry with correct values

## 4. Register SQLAlchemy `before_update` Event

- [ ] 4.1 Register `@event.listens_for(Asset, 'before_update')` to automatically call `record_valuation_change()` when `current_value` or `purchase_price` changes — verify: updating `asset.current_value` creates a `ValuationHistory` record without explicit method call
- [ ] 4.2 Register `@event.listens_for(Liability, 'before_update')` to automatically call `record_valuation_change()` when `remaining_balance` changes — verify: updating `liability.remaining_balance` creates a `ValuationHistory` record

## 5. Add `current_value` and `progress_percentage` to FinancialGoal

- [ ] 5.1 Add `current_value` column to `FinancialGoal` model (DECIMAL(18,2), default 0) — verify: `FinancialGoal` has `current_value` attribute
- [ ] 5.2 Add `progress_percentage` property to `FinancialGoal` — returns `(current_value / target_amount) * 100`, handles `target_amount = 0` — verify: property returns correct percentage for various inputs

## 6. Add `effective_currency` Property

- [ ] 6.1 Add `effective_currency` property to `Asset`, `Liability`, `Income`, and `Expense` classes — returns `'RUB'` when `currency` is `None` — verify: all four models return `'RUB'` when `currency` is `None`

## 7. Wire Stale Records into Dashboard

- [ ] 7.1 Add `/api/stale-records` endpoint in `main.py` that calls `get_stale_records(session)` — verify: endpoint returns list of stale assets and liabilities with their IDs, names, and days since valuation
- [ ] 7.2 Add `/api/goals/progress` endpoint in `main.py` that returns all goals with their `progress_percentage` — verify: endpoint returns goals with calculated progress

## 8. Tests

- [ ] 8.1 Write unit test: `test_asset_is_stale_with_null_date` — verify: `Asset` with `valuation_date = None` has `is_stale == True`
- [ ] 8.2 Write unit test: `test_asset_is_stale_with_old_date` — verify: `Asset` with `valuation_date` > 90 days old has `is_stale == True`
- [ ] 8.3 Write unit test: `test_asset_is_not_stale_with_recent_date` — verify: `Asset` with `valuation_date` within 90 days has `is_stale == False`
- [ ] 8.4 Write unit test: `test_valuation_history_created_on_asset_update` — verify: updating `asset.current_value` creates a `ValuationHistory` record
- [ ] 8.5 Write unit test: `test_valuation_history_preserved_on_asset_deletion` — verify: deleting an asset preserves its history with `asset_id = NULL`
- [ ] 8.6 Write unit test: `test_goal_progress_percentage_calculation` — verify: `FinancialGoal.progress_percentage` returns correct percentage
- [ ] 8.7 Write unit test: `test_goal_progress_zero_target` — verify: `FinancialGoal` with `target_amount = 0` returns `progress_percentage == 0`
- [ ] 8.8 Write unit test: `test_effective_currency_returns_rub_for_none` — verify: all four models return `'RUB'` when `currency` is `None`
- [ ] 8.9 Write integration test: `test_stale_records_api_endpoint` — verify: `/api/stale-records` returns correct stale records
- [ ] 8.10 Write integration test: `test_goals_progress_api_endpoint` — verify: `/api/goals/progress` returns goals with calculated progress
