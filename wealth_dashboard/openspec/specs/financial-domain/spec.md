# financial-domain Specification

## Purpose
TBD - created by archiving change implement-financial-domain-logic. Update Purpose after archive.

## Requirements

### Requirement: Stale Valuation Warning

Every financial record (asset and liability) SHALL be flagged as potentially stale when its `valuation_date` is more than 90 days old or missing.

#### Scenario: Asset with no valuation date is stale

- **WHEN** an asset has `valuation_date = NULL`
- **THEN** `asset.is_stale` returns `True`

#### Scenario: Asset with valuation date older than 90 days is stale

- **WHEN** an asset's `valuation_date` is more than 90 days before the current date
- **THEN** `asset.is_stale` returns `True`

#### Scenario: Asset with recent valuation date is not stale

- **WHEN** an asset's `valuation_date` is within the last 90 days
- **THEN** `asset.is_stale` returns `False`

#### Scenario: Liability with no valuation date is stale

- **WHEN** a liability has `valuation_date = NULL`
- **THEN** `liability.is_stale` returns `True`

#### Scenario: Get all stale records

- **WHEN** the dashboard requests stale records
- **THEN** `get_stale_records(session)` returns all stale assets and liabilities

### Requirement: Valuation History Recording

The system SHALL automatically create `ValuationHistory` records when an asset's `current_value` or `purchase_price` changes.

#### Scenario: Asset value change creates history

- **WHEN** an asset's `current_value` or `purchase_price` is updated
- **THEN** the system automatically creates a `ValuationHistory` record with the old value, new value, change date, and change reason
- **AND** the history record uses `DECIMAL(18,2)` precision for `old_value` and `new_value`

#### Scenario: Liability value change creates history

- **WHEN** a liability's `remaining_balance` is updated
- **THEN** the system automatically creates a `ValuationHistory` record

#### Scenario: Non-value field changes do not create history

- **WHEN** an asset's `name` or `category` is updated (but `current_value` and `purchase_price` are unchanged)
- **THEN** no `ValuationHistory` record is created

#### Scenario: History is preserved when asset is deleted

- **WHEN** an asset is deleted
- **THEN** its `ValuationHistory` records remain but `asset_id` is set to `NULL`

### Requirement: Financial Goal Progress

The system SHALL calculate and expose the progress percentage for each financial goal.

#### Scenario: Progress percentage calculation

- **WHEN** a financial goal has `current_value` and `target_amount`
- **THEN** `goal.progress_percentage` returns `(current_value / target_amount) * 100`

#### Scenario: Zero target amount returns 0% progress

- **WHEN** a financial goal has `target_amount = 0`
- **THEN** `goal.progress_percentage` returns `0` (no division by zero error)

#### Scenario: Progress is 100% when current equals target

- **WHEN** a financial goal's `current_value` equals `target_amount`
- **THEN** `goal.progress_percentage` returns `100.0`

#### Scenario: Progress exceeds 100% when over-funded

- **WHEN** a financial goal's `current_value` exceeds `target_amount`
- **THEN** `goal.progress_percentage` returns a value greater than `100.0`

### Requirement: Effective Currency

Every financial model SHALL expose an `effective_currency` property that returns `'RUB'` when the raw `currency` column is `None`.

#### Scenario: Asset with explicit currency returns it

- **WHEN** an asset has `currency = 'USD'`
- **THEN** `asset.effective_currency` returns `'USD'`

#### Scenario: Asset with NULL currency returns 'RUB'

- **WHEN** an asset has `currency = NULL` (pre-migration data)
- **THEN** `asset.effective_currency` returns `'RUB'`

#### Scenario: Liability with NULL currency returns 'RUB'

- **WHEN** a liability has `currency = NULL` (pre-migration data)
- **THEN** `liability.effective_currency` returns `'RUB'`

#### Scenario: Income with NULL currency returns 'RUB'

- **WHEN** an income record has `currency = NULL` (pre-migration data)
- **THEN** `income.effective_currency` returns `'RUB'`

#### Scenario: Expense with NULL currency returns 'RUB'

- **WHEN** an expense record has `currency = NULL` (pre-migration data)
- **THEN** `expense.effective_currency` returns `'RUB'`
