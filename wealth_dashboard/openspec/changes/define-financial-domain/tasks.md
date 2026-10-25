# Tasks

## 1. Update Asset Model

- [ ] 1.1 Add `valuation_date` column (DateTime, nullable, defaults to `datetime.utcnow`) — verify: `Asset` has `valuation_date` attribute
- [ ] 1.2 Add `currency` column (String, nullable, defaults to 'RUB') — verify: `Asset` has `currency` attribute with default 'RUB'

## 2. Update Liability Model

- [ ] 2.1 Add `valuation_date` column (DateTime, nullable, defaults to `datetime.utcnow`) — verify: `Liability` has `valuation_date` attribute
- [ ] 2.2 Add `currency` column (String, nullable, defaults to 'RUB') — verify: `Liability` has `currency` attribute with default 'RUB'

## 3. Update Income Model

- [ ] 3.1 Add `currency` column (String, nullable, defaults to 'RUB') — verify: `Income` has `currency` attribute with default 'RUB'

## 4. Update Expense Model

- [ ] 4.1 Add `currency` column (String, nullable, defaults to 'RUB') — verify: `Expense` has `currency` attribute with default 'RUB'

## 5. Add ValuationHistory Model

- [ ] 5.1 Create `ValuationHistory` table with: `id`, `asset_id` (FK to assets), `liability_id` (FK to liabilities, nullable), `field_name`, `old_value`, `new_value`, `changed_at`, `change_reason` — verify: `ValuationHistory` model exists with all columns
- [ ] 5.2 Add foreign key constraints to `assets` and `liabilities` tables — verify: foreign keys are defined

## 6. Add FinancialGoal Model

- [ ] 6.1 Create `FinancialGoal` table with: `id`, `name`, `target_amount`, `target_date`, `currency`, `description`, `notes` — verify: `FinancialGoal` model exists with all columns

## 7. Initialize New Tables

- [ ] 7.1 Run `Base.metadata.create_all(engine)` to create new tables — verify: `valuation_history` and `financial_goals` tables exist in SQLite database
