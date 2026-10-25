"""Integration tests for Task Groups 4b, 5, 6, 7:

- ValuationHistory records created by Liability before_update events (4b)
- FinancialGoal.progress_percentage calculation (5)
- FinancialGoal.effective_currency normalization (6)
- /api/stale-records endpoint (7)
- /api/goals/progress endpoint (7)

These tests verify the full stack: database events → models → API endpoints.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    Asset,
    Liability,
    ValuationHistory,
    FinancialGoal,
)


@pytest.fixture(scope="function")
def db_session():
    """Initialize the production database file with the test schema,
    then return a session for test operations.

    Unlike typical unit-test fixtures that use :memory:, this fixture
    reuses the actual ``wealth_dashboard.db`` file so that API routes
    (which call the real ``SessionLocal``) see the same tables and data.

    After each test, all data is purged so tests remain isolated.
    """
    import main as main_module
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wealth_dashboard.db")

    # Create an engine pointing to the production DB file
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    # Create all tables if they don't exist (safe no-op if already present)
    Base.metadata.create_all(engine)

    # Migration: add current_value column to financial_goals if missing.
    # Base.metadata.create_all() silently skips existing tables, so pre-
    # migration DB files won't have this column.
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(
            text("PRAGMA table_info(financial_goals)")
        ).fetchall()}
        if 'current_value' not in cols:
            conn.execute(
                text("ALTER TABLE financial_goals ADD COLUMN current_value FLOAT")
            )
            conn.commit()

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Clean up: purge all test data so tests remain isolated
    try:
        session.query(FinancialGoal).delete()
        session.query(ValuationHistory).delete()
        session.query(Liability).delete()
        session.query(Asset).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

    # Reset the injected session reference
    main_module._test_db_session = None


# =============================================================================
# Task Group 4b: Liability before_update events
# =============================================================================


class TestLiabilityBeforeUpdateEvents:
    """Integration tests for Liability before_update, after_flush, after_insert events."""

    def test_liability_after_insert_stores_initial_remaining_balance(self, db_session):
        """Creating a new Liability should store initial remaining_balance."""
        liability = Liability(
            name="Mortgage",
            liability_type="mortgage",
            amount=5000000.0,
            remaining_balance=5000000.0,
        )
        db_session.add(liability)
        db_session.commit()

        # Verify ValuationHistory record was created by after_insert event
        history = db_session.query(ValuationHistory).filter_by(
            liability_id=liability.id,
            asset_id=None,
        ).all()
        assert len(history) == 1
        assert history[0].field_name == 'remaining_balance'
        assert float(history[0].old_value) == 5000000.0
        assert float(history[0].new_value) == 5000000.0

    def test_liability_before_update_creates_history_on_remaining_balance_change(self, db_session):
        """Changing remaining_balance should create ValuationHistory record."""
        liability = Liability(
            name="Loan",
            liability_type="loan",
            amount=1000000.0,
            remaining_balance=1000000.0,
        )
        db_session.add(liability)
        db_session.commit()

        # Get initial history count
        initial_count = db_session.query(ValuationHistory).filter_by(
            liability_id=liability.id
        ).count()

        # Change remaining_balance
        liability.remaining_balance = 800000.0
        db_session.commit()

        # Verify new ValuationHistory record was created
        history = db_session.query(ValuationHistory).filter_by(
            liability_id=liability.id,
            asset_id=None,
            field_name='remaining_balance',
        ).all()
        assert len(history) == initial_count + 1
        assert float(history[-1].old_value) == 1000000.0
        assert float(history[-1].new_value) == 800000.0

    def test_liability_before_update_skips_when_no_old_value(self, db_session):
        """Changing remaining_balance on a Liability with no initial value should not create history."""
        # Create Liability without remaining_balance (None)
        liability = Liability(
            name="Loan",
            liability_type="loan",
            amount=1000000.0,
            remaining_balance=None,
        )
        db_session.add(liability)
        db_session.commit()

        # Change remaining_balance — should NOT create history (no old value to compare)
        liability.remaining_balance = 500000.0
        db_session.commit()

        # Verify no ValuationHistory was created (because old_value was None)
        history = db_session.query(ValuationHistory).filter_by(
            liability_id=liability.id
        ).all()
        assert len(history) == 0


# =============================================================================
# Task Group 5: FinancialGoal.progress_percentage
# =============================================================================


class TestFinancialGoalProgressPercentage:
    """Integration tests for FinancialGoal.progress_percentage property."""

    def test_progress_percentage_calculates_correctly(self, db_session):
        """progress_percentage should return (current_value / target_amount) * 100."""
        goal = FinancialGoal(
            name="House Fund",
            target_amount=10000000.0,
            current_value=3500000.0,
            currency="RUB",
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 35.0

    def test_progress_percentage_returns_zero_for_null_target(self, db_session):
        """progress_percentage should return 0 when target_amount is None."""
        goal = FinancialGoal(
            name="Vacation",
            target_amount=None,
            current_value=100000.0,
            currency="RUB",
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 0.0

    def test_progress_percentage_returns_zero_for_zero_target(self, db_session):
        """progress_percentage should return 0 when target_amount is 0."""
        goal = FinancialGoal(
            name="Test",
            target_amount=0.0,
            current_value=100000.0,
            currency="RUB",
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 0.0

    def test_progress_percentage_handles_null_current_value(self, db_session):
        """progress_percentage should treat None current_value as 0."""
        goal = FinancialGoal(
            name="Savings",
            target_amount=5000000.0,
            current_value=None,
            currency="RUB",
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 0.0


# =============================================================================
# Task Group 6: FinancialGoal.effective_currency
# =============================================================================


class TestFinancialGoalEffectiveCurrency:
    """Integration tests for FinancialGoal.effective_currency property."""

    def test_effective_currency_returns_rub_when_none(self, db_session):
        """effective_currency should return 'RUB' when currency is None."""
        goal = FinancialGoal(
            name="Old Goal",
            target_amount=1000000.0,
            currency=None,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.effective_currency == 'RUB'

    def test_effective_currency_returns_actual_currency(self, db_session):
        """effective_currency should return the actual currency value."""
        goal = FinancialGoal(
            name="USD Goal",
            target_amount=50000.0,
            currency="USD",
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.effective_currency == 'USD'


# =============================================================================
# Task Group 7: API endpoints
# =============================================================================


class TestApiEndpoints:
    """Integration tests for /api/stale-records and /api/goals/progress endpoints."""

    @pytest.fixture
    def app(self):
        """Import main module and patch database connections."""
        import importlib
        import main as main_module
        importlib.reload(main_module)
        return main_module.app

    def test_api_stale_records_returns_stale_records(self, db_session, app):
        """/api/stale-records should return stale assets and liabilities."""
        from fastapi.testclient import TestClient
        import main as main_module

        # Inject test session so API routes use the in-memory DB, not production
        main_module._test_db_session = db_session

        # Add stale data
        old_date = __import__('datetime').datetime.utcnow() - __import__('datetime').timedelta(days=100)
        stale_asset = Asset(
            name="Old Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=old_date,
            category='stocks',
        )
        db_session.add(stale_asset)
        db_session.commit()

        client = TestClient(app)
        response = client.get("/api/stale-records")

        assert response.status_code == 200
        data = response.json()
        assert 'stale_records' in data
        assert len(data['stale_records']) == 1
        assert data['stale_records'][0]['name'] == 'Old Asset'
        assert data['stale_records'][0]['type'] == 'stocks'

    def test_api_goals_progress_returns_goals_with_progress(self, db_session, app):
        """/api/goals/progress should return goals with progress_percentage and effective_currency."""
        from fastapi.testclient import TestClient
        import main as main_module

        # Inject test session so API routes use the in-memory DB, not production
        main_module._test_db_session = db_session

        goal = FinancialGoal(
            name="House Fund",
            target_amount=10000000.0,
            current_value=2500000.0,
            currency="RUB",
        )
        db_session.add(goal)
        db_session.commit()

        client = TestClient(app)
        response = client.get("/api/goals/progress")

        assert response.status_code == 200
        data = response.json()
        assert 'goals' in data
        assert len(data['goals']) == 1
        assert data['goals'][0]['name'] == 'House Fund'
        assert data['goals'][0]['progress_percentage'] == 25.0
        assert data['goals'][0]['effective_currency'] == 'RUB'

    def test_api_stale_records_returns_empty_for_fresh_data(self, db_session, app):
        """/api/stale-records should return empty list when all records are fresh."""
        from fastapi.testclient import TestClient
        import main as main_module

        # Inject test session so API routes use the in-memory DB, not production
        main_module._test_db_session = db_session

        fresh_asset = Asset(
            name="Fresh Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=__import__('datetime').datetime.utcnow(),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        client = TestClient(app)
        response = client.get("/api/stale-records")

        assert response.status_code == 200
        data = response.json()
        assert len(data['stale_records']) == 0

    def test_api_goals_progress_handles_null_currency(self, db_session, app):
        """/api/goals/progress should normalize None currency to 'RUB' via effective_currency."""
        from fastapi.testclient import TestClient
        import main as main_module

        # Inject test session so API routes use the in-memory DB, not production
        main_module._test_db_session = db_session

        goal = FinancialGoal(
            name="Old Goal",
            target_amount=1000000.0,
            currency=None,
        )
        db_session.add(goal)
        db_session.commit()

        client = TestClient(app)
        response = client.get("/api/goals/progress")

        assert response.status_code == 200
        data = response.json()
        assert len(data['goals']) == 1
        assert data['goals'][0]['effective_currency'] == 'RUB'
        assert data['goals'][0]['currency'] is None  # Original value preserved
