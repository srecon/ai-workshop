# Implementation Plan: `implement-financial-domain-logic`

## Overview

This plan implements the behavioral layer on top of the `define-financial-domain-schema` schema. It adds staleness warnings, automatic valuation history recording, financial goal progress tracking, and effective currency handling.

**Dependency:** `define-financial-domain-schema` must be applied first (tables and columns must exist).

**Estimated effort:** 8–12 hours

**Files modified:** `models.py` (properties, methods, events), `main.py` (API endpoints), `metrics.py` (stale records helper)

**Files created:** `tests/test_financial_domain_logic.py` (10 tests)

---

## Task Group 1: `is_stale` Property (Asset + Liability)

**Dependencies:** None (schema must exist, provided by `define-financial-domain-schema`)

**What to implement:**

Add an `is_stale` property to both `Asset` and `Liability` classes in `models.py`. The property returns `True` when `valuation_date` is `None` or more than 90 days before `datetime.utcnow()`.

**Design decision needed:** Should `valuation_date = None` be treated as stale or fresh?

- **Option A (treat as stale):** A record with no valuation date is unknown — assume it's stale. This is the safer default and aligns with FR-007 ("identify stale valuations").
- **Option B (treat as fresh):** A record with no valuation date hasn't been assessed yet — don't flag it. This risks hiding stale data.

**Recommendation:** Option A (treat as stale). Unknown data is worse than stale data because the user can't make informed decisions.

**Code change (models.py):**

```python
# Add to Asset class (after existing properties)
@property
def is_stale(self, max_days=90):
    """Returns True if valuation_date is None or older than 90 days."""
    if self.valuation_date is None:
        return True
    delta = datetime.datetime.utcnow() - self.valuation_date
    return delta.days > max_days

# Add to Liability class (same logic)
@property
def is_stale(self, max_days=90):
    if self.valuation_date is None:
        return True
    delta = datetime.datetime.utcnow() - self.valuation_date
    return delta.days > max_days
```

**Test (test_financial_domain_logic.py):**

```python
def test_asset_is_stale_with_null_date():
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0, valuation_date=None)
    assert asset.is_stale is True

def test_asset_is_stale_with_old_date():
    old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0, valuation_date=old_date)
    assert asset.is_stale is True

def test_asset_is_not_stale_with_recent_date():
    recent_date = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0, valuation_date=recent_date)
    assert asset.is_stale is False
```

**Verification command:** `python -c "from models import Asset; import datetime; a = Asset(name='T', purchase_price=1.0, current_value=1.0, valuation_date=None); print(a.is_stale)"` (expect `True`)

---

## Task Group 2: `get_stale_records` Helper

**Dependencies:** Task Group 1 (`is_stale` property must exist)

**What to implement:**

Add a `get_stale_records(session)` function. The spec says "the dashboard requests stale records" — this is a query helper, not an API endpoint. It should return all stale assets and liabilities.

**Design decision needed:** Where should this function live?

- **Option A (`metrics.py`):** Co-locate with other query helpers. But `MetricsCalculator` is a class that operates on dicts, not models. Adding a function that operates on models would mix paradigms.
- **Option B (`models.py`):** Add as a module-level function next to the models. This keeps it close to the `is_stale` property it depends on.
- **Option C (new `stale_checker.py`):** Dedicated module for staleness logic. Clean separation but adds file count.

**Recommendation:** Option B (`models.py`). The function depends on `is_stale` which lives on the models. Adding it to `models.py` as a module-level function keeps the dependency graph simple.

**Code change (models.py):**

```python
def get_stale_records(session, max_days=90):
    """Return all stale assets and liabilities."""
    stale_assets = []
    for asset in session.query(Asset).all():
        if asset.is_stale(max_days):
            stale_assets.append({
                'type': 'asset',
                'id': asset.id,
                'name': asset.name,
                'valuation_date': asset.valuation_date.isoformat() if asset.valuation_date else None,
                'days_since_valuation': (datetime.datetime.utcnow() - asset.valuation_date).days if asset.valuation_date else None
            })

    stale_liabilities = []
    for liability in session.query(Liability).all():
        if liability.is_stale(max_days):
            stale_liabilities.append({
                'type': 'liability',
                'id': liability.id,
                'name': liability.name,
                'valuation_date': liability.valuation_date.isoformat() if liability.valuation_date else None,
                'days_since_valuation': (datetime.datetime.utcnow() - liability.valuation_date).days if liability.valuation_date else None
            })

    return stale_assets + stale_liabilities
```

**Test:**

```python
def test_get_stale_records_returns_stale_assets_and_liabilities():
    old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    stale_asset = Asset(name="Old", purchase_price=100000.0, current_value=110000.0, valuation_date=old_date)
    fresh_asset = Asset(name="Fresh", purchase_price=200000.0, current_value=210000.0, valuation_date=datetime.datetime.utcnow())
    session.add_all([stale_asset, fresh_asset])
    session.commit()

    stale = get_stale_records(session)
    assert len(stale) == 1
    assert stale[0]['name'] == 'Old'
```

**Verification command:** `python -c "from models import get_stale_records; print(type(get_stale_records))"` (expect `<class 'function'>`)

---

## Task Group 3: `record_valuation_change` Method

**Dependencies:** Task Group 1 (`is_stale` property), schema change (`ValuationHistory` table must exist)

**What to implement:**

Add a `record_valuation_change(session, field_name, change_reason)` method to `Asset` and `Liability` classes. This method creates a `ValuationHistory` record with the old value, new value, timestamp, and optional reason.

**Design decision needed:** How does the method know which field changed?

- **Option A (explicit):** The caller passes `field_name` (e.g., `'current_value'`). The method reads `getattr(self, field_name)` as the new value and `self.__dict__.get('_old_' + field_name)` as the old value. The caller is responsible for capturing the old value before the update.
- **Option B (automatic via event):** The `before_update` SQLAlchemy event (Task Group 4) captures the old value and calls this method. The method itself doesn't need to know which field changed — the event passes it.

**Recommendation:** Option B. Task Group 4 (the event listener) is the natural owner of "which field changed" knowledge. The `record_valuation_change` method is a helper that the event calls. The method signature should be:

```python
def record_valuation_change(self, session, field_name, old_value, new_value, change_reason=None):
    """Create a ValuationHistory record for a field change."""
    history = ValuationHistory(
        asset_id=self.id if hasattr(self, 'asset_id') else None,
        liability_id=self.id if hasattr(self, 'liability_id') else None,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_at=datetime.datetime.utcnow(),
        change_reason=change_reason
    )
    session.add(history)
```

**Note:** This method is called by the event listener (Task Group 4), not by application code. It's an internal helper.

**Test:**

```python
def test_record_valuation_change_creates_history():
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0)
    session.add(asset)
    session.commit()

    asset.record_valuation_change(session, 'current_value', 110000.0, 120000.0, "Manual update")
    session.commit()

    history = session.query(ValuationHistory).filter_by(asset_id=asset.id).first()
    assert history is not None
    assert history.field_name == 'current_value'
    assert float(history.old_value) == 110000.0
    assert float(history.new_value) == 120000.0
```

**Verification command:** `python -c "from models import Asset; print(hasattr(Asset, 'record_valuation_change'))"` (expect `True`)

---

## Task Group 4: SQLAlchemy `before_update` Event

**Dependencies:** Task Group 3 (`record_valuation_change` method must exist)

**What to implement:**

Register a SQLAlchemy `@event.listens_for(Asset, 'before_update')` that automatically calls `record_valuation_change()` when `current_value` or `purchase_price` changes. Similarly for `Liability` when `remaining_balance` changes.

**Design decision needed:** Where to register the event?

- **Option A (`models.py` at module level):** Register events when the module is imported. Simple, but events are registered every time `models.py` is imported (including in tests). This can cause "event already registered" warnings.
- **Option B (in a separate `events.py` module):** Register events in an `init_events()` function that's called once at application startup (from `main.py`). Cleaner separation, explicit lifecycle.
- **Option C (in `main.py` startup):** Register events in the FastAPI `@app.on_event("startup")` handler. Ties event registration to the application lifecycle.

**Recommendation:** Option B (`events.py` module). Create a new file `events.py` that exports an `init_events()` function. Call it once from `main.py` at startup. This gives explicit lifecycle control and avoids duplicate registration in tests.

**Code change (new file `events.py`):**

```python
from sqlalchemy import event
from models import Asset, Liability, ValuationHistory, SessionLocal

def init_events():
    """Register before_update events for Asset and Liability models."""

    @event.listens_for(Asset, 'before_update')
    def capture_asset_history(mapper, connection, target):
        _capture_history(target, connection, 'asset_id', 'current_value', 'purchase_price')
        _capture_history(target, connection, 'asset_id', 'purchase_price', 'purchase_price')

    @event.listens_for(Liability, 'before_update')
    def capture_liability_history(mapper, connection, target):
        _capture_history(target, connection, 'liability_id', 'remaining_balance', 'remaining_balance')


def _capture_history(target, connection, id_field, *fields_to_track):
    """Internal helper: capture history for tracked fields that changed."""
    # This is called by SQLAlchemy before the update is committed.
    # We need to compare the in-memory value with the database value.
    # SQLAlchemy's `attributes.get` gives us the old value before the update.
    from sqlalchemy import inspect
    from models import sessionmaker

    # Get the old values from SQLAlchemy's history tracking
    inspector = inspect(target)
    for field_name in fields_to_track:
        history = inspector.attrs.get(field_name).history
        if history.has_changes():
            old_value = history.deleted[0] if history.deleted else None
            new_value = getattr(target, field_name)
            if old_value is not None and new_value is not None:
                # Create ValuationHistory record
                db = sessionmaker()
                try:
                    history_record = ValuationHistory(
                        **{id_field: getattr(target, id_field)},
                        field_name=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        changed_at=datetime.datetime.utcnow()
                    )
                    db.add(history_record)
                    # Don't commit here — the main transaction handles that
                finally:
                    db.close()
```

**Wait — there's a critical design issue here.** The `before_update` event fires **before** the ORM flushes the change to the database. At this point, `target.current_value` already has the **new** value in Python memory, but the old value is stored in SQLAlchemy's internal history. We need to access `inspector.attrs.get('current_value').history.deleted` to get the old value.

However, there's a subtlety: if the user creates a new asset (not an update), `before_update` won't fire. We need a separate `before_insert` event to capture the initial valuation.

**Revised design:**

```python
@event.listens_for(Asset, 'before_insert')
def capture_asset_insert(mapper, connection, target):
    """Capture initial valuation when an asset is first created."""
    if target.current_value is not None and target.purchase_price is not None:
        db = sessionmaker()
        try:
            history = ValuationHistory(
                asset_id=target.id,  # Note: id may not be set yet at insert time
                field_name='initial_value',
                old_value=target.purchase_price,
                new_value=target.current_value,
                changed_at=datetime.datetime.utcnow(),
                change_reason='Initial valuation'
            )
            db.add(history)
        finally:
            db.close()
```

**Note:** At `before_insert` time, `target.id` may not be set yet (it's auto-generated). We need to handle this by querying the asset after commit, or by using a different approach.

**Alternative approach:** Instead of `before_insert`/`before_update` events, use a simpler pattern: track changes in the `__init__` and `__setattr__` methods, or use a `session.commit()` hook. But these are more invasive.

**Recommendation:** Use `before_update` only (not `before_insert`). The initial valuation doesn't need history — history starts when the value changes for the first time. If the user wants initial valuation history, that's a Phase 4 feature.

**Test:**

```python
def test_valuation_history_created_on_asset_update():
    """Updating an asset's current_value should auto-create a ValuationHistory record."""
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0)
    session.add(asset)
    session.commit()

    # Update current_value — the before_update event should create history
    asset.current_value = 120000.0
    session.commit()

    history_count = session.query(ValuationHistory).filter_by(asset_id=asset.id).count()
    assert history_count == 1

    history = session.query(ValuationHistory).filter_by(asset_id=asset.id).first()
    assert history.field_name == 'current_value'
    assert float(history.old_value) == 110000.0
    assert float(history.new_value) == 120000.0

def test_non_value_field_changes_do_not_create_history():
    """Updating name or category should NOT create ValuationHistory."""
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0)
    session.add(asset)
    session.commit()

    asset.name = "Updated Name"
    session.commit()

    history_count = session.query(ValuationHistory).filter_by(asset_id=asset.id).count()
    assert history_count == 0
```

**Verification command:** Start the app, create an asset, update its value, check the `valuation_history` table.

---

## Task Group 5: `current_value` and `progress_percentage` on FinancialGoal

**Dependencies:** Schema change (`FinancialGoal` table with `current_value` column must exist)

**What to implement:**

Add a `progress_percentage` property to `FinancialGoal` that calculates `(current_value / target_amount) * 100`. Handle edge cases: `target_amount = 0` returns 0, `current_value > target_amount` returns > 100.

**Code change (models.py):**

```python
@property
def progress_percentage(self):
    """Calculate progress as percentage. Returns 0 if target_amount is 0."""
    if self.target_amount is None or self.target_amount == 0:
        return 0.0
    current = float(self.current_value or 0)
    target = float(self.target_amount)
    return (current / target) * 100
```

**Test:**

```python
def test_goal_progress_percentage_calculation():
    goal = FinancialGoal(name="Test", target_amount=1000000.0, current_value=350000.0)
    session.add(goal)
    session.commit()
    assert goal.progress_percentage == 35.0

def test_goal_progress_zero_target():
    goal = FinancialGoal(name="Test", target_amount=0.0, current_value=500000.0)
    session.add(goal)
    session.commit()
    assert goal.progress_percentage == 0.0

def test_goal_progress_100_percent():
    goal = FinancialGoal(name="Test", target_amount=1000000.0, current_value=1000000.0)
    session.add(goal)
    session.commit()
    assert goal.progress_percentage == 100.0

def test_goal_progress_over_100_percent():
    goal = FinancialGoal(name="Test", target_amount=1000000.0, current_value=1500000.0)
    session.add(goal)
    session.commit()
    assert goal.progress_percentage == 150.0
```

**Verification command:** `python -c "from models import FinancialGoal; g = FinancialGoal(name='T', target_amount=100.0, current_value=50.0); print(g.progress_percentage)"` (expect `50.0`)

---

## Task Group 6: `effective_currency` Property

**Dependencies:** Schema change (`currency` column must exist on all models)

**What to implement:**

Add an `effective_currency` property to `Asset`, `Liability`, `Income`, and `Expense` classes. Returns `'RUB'` when `currency` is `None` (pre-migration data).

**Code change (models.py):**

```python
# Add to Asset class
@property
def effective_currency(self):
    return self.currency if self.currency else 'RUB'

# Add to Liability class
@property
def effective_currency(self):
    return self.currency if self.currency else 'RUB'

# Add to Income class
@property
def effective_currency(self):
    return self.currency if self.currency else 'RUB'

# Add to Expense class
@property
def effective_currency(self):
    return self.currency if self.currency else 'RUB'
```

**Test:**

```python
def test_effective_currency_returns_explicit_value():
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0, currency='USD')
    session.add(asset)
    session.commit()
    assert asset.effective_currency == 'USD'

def test_effective_currency_returns_rub_for_none():
    asset = Asset(name="Test", purchase_price=100000.0, current_value=110000.0, currency=None)
    session.add(asset)
    session.commit()
    assert asset.effective_currency == 'RUB'
```

**Verification command:** `python -c "from models import Asset; a = Asset(name='T', purchase_price=1.0, current_value=1.0, currency=None); print(a.effective_currency)"` (expect `'RUB'`)

---

## Task Group 7: API Endpoints

**Dependencies:** Task Group 2 (`get_stale_records` helper must exist)

**What to implement:**

Add two FastAPI endpoints to `main.py`:

1. `/api/stale-records` — returns all stale assets and liabilities
2. `/api/goals/progress` — returns all financial goals with their progress percentage

**Design decision needed:** Response format for stale records.

- **Option A (flat list):** Return a single list of `{type, id, name, valuation_date, days_since_valuation}`. Simple, easy to consume.
- **Option B (nested):** Return `{assets: [...], liabilities: [...]}`. Separates concerns but adds nesting.

**Recommendation:** Option A (flat list). The UI can group by type if needed. A flat list is simpler for the dashboard to render.

**Code change (main.py):**

```python
from models import get_stale_records

@app.get("/api/stale-records")
async def stale_records_endpoint():
    """Return all stale assets and liabilities."""
    db = SessionLocal()
    try:
        stale = get_stale_records(db)
        return JSONResponse({'stale_records': stale})
    finally:
        db.close()

@app.get("/api/goals/progress")
async def goals_progress_endpoint():
    """Return all financial goals with their progress percentage."""
    from models import FinancialGoal
    db = SessionLocal()
    try:
        goals = db.query(FinancialGoal).all()
        result = []
        for goal in goals:
            result.append({
                'id': goal.id,
                'name': goal.name,
                'target_amount': float(goal.target_amount) if goal.target_amount else 0,
                'current_value': float(goal.current_value) if goal.current_value else 0,
                'target_date': goal.target_date.isoformat() if goal.target_date else None,
                'currency': goal.currency,
                'progress_percentage': goal.progress_percentage,
                'description': goal.description
            })
        return JSONResponse({'goals': result})
    finally:
        db.close()
```

**Test:**

```python
def test_stale_records_api_endpoint(client):
    """POST /api/stale-records returns stale records."""
    old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    stale_asset = Asset(name="Old", purchase_price=100000.0, current_value=110000.0, valuation_date=old_date)
    session.add(stale_asset)
    session.commit()

    response = client.get("/api/stale-records")
    assert response.status_code == 200
    data = response.json()
    assert len(data['stale_records']) == 1
    assert data['stale_records'][0]['name'] == 'Old'

def test_goals_progress_api_endpoint(client):
    """GET /api/goals/progress returns goals with progress."""
    goal = FinancialGoal(name="Test", target_amount=1000000.0, current_value=350000.0)
    session.add(goal)
    session.commit()

    response = client.get("/api/goals/progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data['goals']) == 1
    assert data['goals'][0]['progress_percentage'] == 35.0
```

**Verification command:** `curl http://localhost:8000/api/stale-records` (expect JSON with stale records)

---

## Task Group 8: Integration Tests

**Dependencies:** All Task Groups above must be implemented

**What to implement:**

End-to-end tests that verify the full flow: create data → update value → check history → check stale → check goal progress.

**Test file:** `tests/test_financial_domain_logic.py`

**Tests:**

| # | Test name | What it verifies | Depends on |
|---|-----------|-------------------|-------------|
| 1 | `test_asset_is_stale_with_null_date` | `is_stale` returns `True` for NULL date | Task Group 1 |
| 2 | `test_asset_is_stale_with_old_date` | `is_stale` returns `True` for >90 days | Task Group 1 |
| 3 | `test_asset_is_not_stale_with_recent_date` | `is_stale` returns `False` for <90 days | Task Group 1 |
| 4 | `test_valuation_history_created_on_asset_update` | `before_update` event creates history | Task Group 4 |
| 5 | `test_valuation_history_preserved_on_asset_deletion` | `ON DELETE SET NULL` preserves history | Schema change |
| 6 | `test_goal_progress_percentage_calculation` | `progress_percentage` returns correct value | Task Group 5 |
| 7 | `test_goal_progress_zero_target` | `progress_percentage` returns 0 for zero target | Task Group 5 |
| 8 | `test_effective_currency_returns_rub_for_none` | `effective_currency` returns 'RUB' for NULL | Task Group 6 |
| 9 | `test_stale_records_api_endpoint` | `/api/stale-records` returns correct data | Task Group 7 |
| 10 | `test_goals_progress_api_endpoint` | `/api/goals/progress` returns correct data | Task Group 7 |

**Verification command:** `python -m pytest tests/test_financial_domain_logic.py -v`

---

## Missing Design Decisions

These decisions were flagged during the review but are not resolved in the artifacts. They must be resolved before implementation:

| # | Decision | Options | Recommendation | Impact if wrong |
|---|----------|---------|----------------|-----------------|
| 1 | How to handle `valuation_date = None` in `is_stale`? | Treat as stale (safe) vs. fresh (permissive) | Treat as stale | If treated as fresh, stale data silently passes — breaks FR-007 |
| 2 | Where to register `before_update` events? | `models.py` (inline) vs. `events.py` (separate module) vs. `main.py` (startup) | Separate `events.py` module | If registered in `models.py`, tests may register events multiple times |
| 3 | How to handle DECIMAL type from SQLite? | Convert strings to `Decimal` in Python vs. cast in SQL | Convert in Python (safer) | If SQLite returns strings and Python treats them as strings, comparisons fail |
| 4 | Should `before_insert` create initial history? | Yes (capture initial valuation) vs. No (history starts on first change) | No (simpler) | If yes, every new asset creates a history record — may be noise |
| 5 | Where does `get_stale_records` live? | `models.py` (module-level) vs. `metrics.py` (with other helpers) vs. new module | `models.py` (module-level) | If in `metrics.py`, it mixes dict-based and model-based paradigms |

---

## Execution Order

```
Task Group 1 (is_stale)
    │
    ├─→ Task Group 2 (get_stale_records)
    │       │
    │       └─→ Task Group 7 (API endpoints)
    │               │
    │               └─→ Task Group 8 (integration tests)
    │
    ├─→ Task Group 3 (record_valuation_change)
    │       │
    │       └─→ Task Group 4 (before_update events)
    │               │
    │               └─→ Task Group 8 (integration tests)
    │
    └─→ Task Group 5 (FinancialGoal progress)
            │
            └─→ Task Group 7 (API endpoints)
                    │
                    └─→ Task Group 8 (integration tests)

Task Group 6 (effective_currency) — independent, can run in parallel with any group
```

**Parallel execution:** Task Groups 1, 5, and 6 can be implemented in parallel (no cross-dependencies). Task Groups 2, 3, and 4 must be sequential. Task Group 7 depends on 2 and 5. Task Group 8 depends on all.

---

## Files Summary

| File | Action | Changes |
|------|--------|---------|
| `models.py` | Modify | Add `is_stale`, `effective_currency`, `record_valuation_change`, `progress_percentage` properties/methods |
| `events.py` | **Create** | New module for SQLAlchemy event registration |
| `main.py` | Modify | Add `/api/stale-records` and `/api/goals/progress` endpoints |
| `tests/test_financial_domain_logic.py` | **Create** | 10 unit + integration tests |

---

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `before_update` event fires with stale ORM state | Medium | Use `inspector.attrs.get(field).history` to access old values, not direct attribute access |
| DECIMAL values from SQLite are strings, not `Decimal` objects | High | Convert explicitly: `float(row['column'])` or `Decimal(str(row['column']))` |
| Event registration in tests creates duplicate listeners | Medium | Use `events.py` module with `init_events()` called once; skip in test fixtures |
| `valuation_date` timezone handling (naive vs. aware) | Low | Use `datetime.datetime.utcnow()` consistently (naive, UTC) — don't mix with timezone-aware datetimes |
| Existing code calls `Asset.current_value` directly — bypasses history | Medium | Document that direct attribute access bypasses history; use `record_valuation_change()` for manual updates |
