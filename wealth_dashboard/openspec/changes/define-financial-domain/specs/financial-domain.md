---
name: Define Financial Domain — Specs
description: Specification for valuation_date, ValuationHistory, currency, and FinancialGoal model changes
type: project
category: code_standard
keywords:
  - "valuation date"
  - "valuation history"
  - "currency field"
  - "financial goal model"
  - "data model spec"
usage_scenarios:
  - "Defining data model specifications for financial applications"
  - "Specifying valuation history tracking requirements"
  - "Defining currency handling specifications"
---

# Spec Delta

## ADDED Requirements

### Requirement: Valuation Date

Every financial record (asset and liability) SHALL track when its value was last assessed.

#### Scenario: Asset has valuation date

- **WHEN** the user creates or updates an asset
- **THEN** the system records the current date as `valuation_date`
- **AND** defaults to today if the user does not specify a date

#### Scenario: Liability has valuation date

- **WHEN** the user creates or updates a liability
- **THEN** the system records the current date as `valuation_date`
- **AND** defaults to today if the user does not specify a date

#### Scenario: Stale valuation warning

- **WHEN** a record's `valuation_date` is more than 90 days old
- **THEN** the system flags it as potentially stale in the dashboard

### Requirement: Valuation History

The system SHALL track value changes for assets and liabilities over time.

#### Scenario: Record valuation on update

- **WHEN** an asset's `current_value` or `purchase_price` changes
- **THEN** the system creates a `ValuationHistory` record with the old values, new values, change date, and change reason

#### Scenario: Query valuation history

- **WHEN** the user requests historical data for an asset
- **THEN** the system returns all `ValuationHistory` records sorted by date

#### Scenario: No history for unchanged records

- **WHEN** an asset or liability record is created but never modified
- **THEN** no `ValuationHistory` records exist until the first value change

### Requirement: Currency Field

Every financial record SHALL store its original currency.

#### Scenario: Asset has currency

- **WHEN** the user creates an asset
- **THEN** the system stores the currency code (e.g., 'RUB', 'USD', 'CNY')
- **AND** defaults to 'RUB' for backward compatibility

#### Scenario: Liability has currency

- **WHEN** the user creates a liability
- **THEN** the system stores the currency code
- **AND** defaults to 'RUB' for backward compatibility

#### Scenario: Income has currency

- **WHEN** the user creates an income record
- **THEN** the system stores the currency code
- **AND** defaults to 'RUB' for backward compatibility

#### Scenario: Expense has currency

- **WHEN** the user creates an expense record
- **THEN** the system stores the currency code
- **AND** defaults to 'RUB' for backward compatibility

### Requirement: Financial Goal Model

The system SHALL support financial goals with target amount, target date, and progress tracking.

#### Scenario: Create a financial goal

- **WHEN** the user creates a financial goal
- **THEN** the system stores: name, target amount, target date, currency, description, and optional notes

#### Scenario: Goal has currency

- **WHEN** the user creates a financial goal
- **THEN** the system stores the currency code
- **AND** defaults to 'RUB' for backward compatibility
