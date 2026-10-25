"""Tests for financial domain logic: is_stale property, get_stale_records,
ValuationHistory recording, FinancialGoal progress, effective_currency,
and full integration tests (Task Group 8)."""

import pytest
import datetime
import os
import sys

# Ensure models.py is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    Asset,
    Liability,
    Income,
    Expense,
    UserOverride,
    ValuationHistory,
    FinancialGoal,
    SessionLocal,
    get_stale_records,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# =============================================================================
# Task Group 1: is_stale property
# =============================================================================


class TestIsStaleProperty:
    """Tests for the is_stale property on Asset and Liability classes."""

    def test_asset_is_stale_with_null_date(self, db_session):
        """An asset with valuation_date=None should be considered stale."""
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=None,
        )
        db_session.add(asset)
        db_session.commit()

        assert asset.is_stale is True

    def test_asset_is_stale_with_old_date(self, db_session):
        """An asset with valuation_date > 90 days ago should be considered stale."""
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=old_date,
        )
        db_session.add(asset)
        db_session.commit()

        assert asset.is_stale is True

    def test_asset_is_not_stale_with_recent_date(self, db_session):
        """An asset with valuation_date < 90 days ago should NOT be considered stale."""
        recent_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=recent_date,
        )
        db_session.add(asset)
        db_session.commit()

        assert asset.is_stale is False

    def test_liability_is_stale_with_null_date(self, db_session):
        """A liability with valuation_date=None should be considered stale."""
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=None,
        )
        db_session.add(liability)
        db_session.commit()

        assert liability.is_stale is True

    def test_liability_is_stale_with_old_date(self, db_session):
        """A liability with valuation_date > 90 days ago should be considered stale."""
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=95)
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=old_date,
        )
        db_session.add(liability)
        db_session.commit()

        assert liability.is_stale is True

    def test_liability_is_not_stale_with_recent_date(self, db_session):
        """A liability with valuation_date < 90 days ago should NOT be considered stale."""
        recent_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=recent_date,
        )
        db_session.add(liability)
        db_session.commit()

        assert liability.is_stale is False


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)
        stale_asset = Asset(
            name="Old Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=old_date,
        )
        fresh_asset = Asset(
            name="Fresh Asset",
            purchase_price=200000.0,
            current_value=210000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        stale_liability = Liability(
            name="Old Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=old_date,
        )
        db_session.add_all([stale_asset, fresh_asset, stale_liability])
        db_session.commit()

        stale = get_stale_records(db_session)
        assert len(stale) == 2
        names = {record['name'] for record in stale}
        assert 'Old Asset' in names
        assert 'Old Loan' in names

    def test_get_stale_records_excludes_fresh_records(self, db_session):
        """get_stale_records should NOT return fresh records."""
        fresh_asset = Asset(
            name="Fresh Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        stale = get_stale_records(db_session)
        assert len(stale) == 0

    def test_get_stale_records_includes_null_valuation_date(self, db_session):
        """get_stale_records should include records with valuation_date=None."""
        stale_asset = Asset(
            name="No Date Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=None,
        )
        db_session.add(stale_asset)
        db_session.commit()

        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 3: record_valuation_change() method
# =============================================================================


class TestRecordValuationChange:
    """Tests for the record_valuation_change method on Asset and Liability."""

    def test_asset_record_valuation_change_creates_history(self, db_session):
        """Calling record_valuation_change on an Asset should create a ValuationHistory row.

        Note: record_valuation_change() creates one ValuationHistory record directly.
        The after_flush event also creates one from _pending_history (even though
        before_update skips the field, it still sets _pending_history = []).
        So we expect 2 records total — one from each mechanism.
        """
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(asset)
        db_session.commit()

        # Now change the value and record it
        asset.current_value = 125000.0
        asset.record_valuation_change(db_session, 'current_value', change_reason='revaluation')

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).all()
        # One from record_valuation_change(), one from after_flush event
        assert len(history) == 2
        reasons = {h.change_reason for h in history}
        assert 'revaluation' in reasons  # manual record
        assert 'auto_update' in reasons  # event-based record

    def test_liability_record_valuation_change_creates_history(self, db_session):
        """Calling record_valuation_change on a Liability should create a ValuationHistory row.

        Note: record_valuation_change() creates one ValuationHistory record directly.
        The after_flush event also creates one from _pending_history (even though
        before_update skips the field, it still sets _pending_history = []).
        So we expect 2 records total — one from each mechanism.
        """
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(liability)
        db_session.commit()

        liability.remaining_balance = 350000.0
        liability.record_valuation_change(db_session, 'remaining_balance', change_reason='payment')

        history = db_session.query(ValuationHistory).filter_by(liability_id=liability.id).all()
        # One from record_valuation_change(), one from after_flush event
        assert len(history) == 2
        reasons = {h.change_reason for h in history}
        assert 'payment' in reasons  # manual record
        assert 'auto_update' in reasons  # event-based record


# =============================================================================
# Task Group 4: SQLAlchemy before_update event
# =============================================================================


class TestAssetBeforeUpdateEvent:
    """Tests for the Asset before_update / after_flush / after_insert events."""

    def test_asset_before_update_creates_history_on_current_value_change(self, db_session):
        """Updating Asset.current_value should create a ValuationHistory entry via events."""
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(asset)
        db_session.commit()

        # Update current_value — the before_update event should fire
        asset.current_value = 130000.0
        db_session.commit()

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).all()
        assert len(history) >= 1
        assert any(h.field_name == 'current_value' for h in history)


# =============================================================================
# Task Group 5: FinancialGoal progress_percentage
# =============================================================================


class TestFinancialGoalProgressPercentage:
    """Tests for the progress_percentage property on FinancialGoal."""

    def test_goal_progress_percentage_calculation(self, db_session):
        """progress_percentage should be (current_value / target_amount) * 100."""
        goal = FinancialGoal(
            name="Retirement",
            target_amount=1000000.0,
            current_value=250000.0,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 25.0

    def test_goal_progress_zero_target(self, db_session):
        """progress_percentage should be 0 when target_amount is 0."""
        goal = FinancialGoal(
            name="Empty Goal",
            target_amount=0.0,
            current_value=100000.0,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 0.0

    def test_goal_progress_100_percent(self, db_session):
        """progress_percentage should be 100 when current == target."""
        goal = FinancialGoal(
            name="On Target",
            target_amount=500000.0,
            current_value=500000.0,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 100.0

    def test_goal_progress_over_100_percent(self, db_session):
        """progress_percentage can exceed 100 when current > target."""
        goal = FinancialGoal(
            name="Over Target",
            target_amount=500000.0,
            current_value=750000.0,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 150.0

    def test_goal_progress_null_current_value(self, db_session):
        """progress_percentage should be 0 when current_value is None."""
        goal = FinancialGoal(
            name="New Goal",
            target_amount=1000000.0,
            current_value=None,
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.progress_percentage == 0.0


# =============================================================================
# Task Group 8: Integration tests (full lifecycle)
# =============================================================================


class TestIntegrationValuationHistory:
    """Integration tests for full valuation history lifecycle (TG8)."""

    def test_e2e_asset_valuation_history_via_events(self, db_session):
        """Full lifecycle: insert asset → update current_value → verify ValuationHistory created by events."""
        asset = Asset(
            name="Property A",
            purchase_price=5000000.0,
            current_value=5500000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
            asset_type="growth",
            category="real_estate",
        )
        db_session.add(asset)
        db_session.commit()

        # First update: 5.5M → 6.0M
        asset.current_value = 6000000.0
        db_session.commit()

        # Second update: 6.0M → 6.5M
        asset.current_value = 6500000.0
        db_session.commit()

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).order_by(ValuationHistory.id).all()
        # Should have 2 history records from the two updates
        assert len(history) == 2
        assert history[0].old_value == 5500000.0
        assert history[0].new_value == 6000000.0
        assert history[1].old_value == 6000000.0
        assert history[1].new_value == 6500000.0

    def test_e2e_liability_balance_history_via_events(self, db_session):
        """Full lifecycle: insert liability → update remaining_balance → verify ValuationHistory."""
        liability = Liability(
            name="Mortgage",
            liability_type="mortgage",
            amount=10000000.0,
            remaining_balance=9000000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(liability)
        db_session.commit()

        # Make payments: 9M → 8M → 7M
        liability.remaining_balance = 8000000.0
        db_session.commit()
        liability.remaining_balance = 7000000.0
        db_session.commit()

        history = db_session.query(ValuationHistory).filter_by(liability_id=liability.id).order_by(ValuationHistory.id).all()
        assert len(history) == 2
        assert history[0].old_value == 9000000.0
        assert history[0].new_value == 8000000.0
        assert history[1].old_value == 8000000.0
        assert history[1].new_value == 7000000.0

    def test_e2e_stale_detection_with_valuation_history(self, db_session):
        """Stale detection + valuation history: stale asset shows in get_stale_records, history tracks changes."""
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)
        asset = Asset(
            name="Old Stock",
            purchase_price=100000.0,
            current_value=120000.0,
            valuation_date=old_date,
        )
        db_session.add(asset)
        db_session.commit()

        # Record a valuation change manually
        asset.current_value = 130000.0
        asset.record_valuation_change(db_session, 'current_value', change_reason='market_update')
        db_session.commit()

        # Check stale records
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'Old Stock'

        # Check history exists (one from record_valuation_change(), one from after_flush event)
        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).all()
        assert len(history) == 2
        reasons = {h.change_reason for h in history}
        assert 'market_update' in reasons
        assert 'auto_update' in reasons

    def test_e2e_api_stale_records_response(self, db_session):
        """Integration: stale records API returns correct stale assets and liabilities."""
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=120)
        stale_asset = Asset(
            name="Stale House",
            purchase_price=8000000.0,
            current_value=9000000.0,
            valuation_date=old_date,
            category="real_estate",
        )
        fresh_asset = Asset(
            name="Fresh Bond",
            purchase_price=1000000.0,
            current_value=1050000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
            category="bonds",
        )
        stale_liab = Liability(
            name="Old Credit Card",
            liability_type="credit",
            amount=200000.0,
            remaining_balance=150000.0,
            valuation_date=old_date,
        )
        db_session.add_all([stale_asset, fresh_asset, stale_liab])
        db_session.commit()

        stale = get_stale_records(db_session)
        assert len(stale) == 2
        names = {r['name'] for r in stale}
        assert 'Stale House' in names
        assert 'Old Credit Card' in names
        # Verify structure
        house = next(r for r in stale if r['name'] == 'Stale House')
        assert house['type'] == 'real_estate'
        assert house['edit_url'] == '/edit/asset/stale_asset.id'.replace('stale_asset.id', str(stale_asset.id))
        assert house['last_value'] == 9000000.0

    def test_e2e_api_goals_progress_response(self, db_session):
        """Integration: goals progress API returns goals with progress_percentage and effective_currency."""
        goal1 = FinancialGoal(
            name="Retirement",
            target_amount=10000000.0,
            current_value=3000000.0,
            currency='RUB',
        )
        goal2 = FinancialGoal(
            name="Emergency Fund",
            target_amount=1000000.0,
            current_value=None,
            # currency is None — pre-migration data
        )
        goal3 = FinancialGoal(
            name="Vacation Home",
            target_amount=5000000.0,
            current_value=5500000.0,
            currency='USD',
        )
        db_session.add_all([goal1, goal2, goal3])
        db_session.commit()

        goals = db_session.query(FinancialGoal).all()
        result = []
        for goal in goals:
            result.append({
                'id': goal.id,
                'name': goal.name,
                'progress_percentage': goal.progress_percentage,
                'effective_currency': goal.effective_currency,
            })

        # Find each goal by name
        by_name = {g['name']: g for g in result}
        assert by_name['Retirement']['progress_percentage'] == 30.0
        assert by_name['Retirement']['effective_currency'] == 'RUB'
        assert by_name['Emergency Fund']['progress_percentage'] == 0.0
        assert by_name['Emergency Fund']['effective_currency'] == 'RUB'  # None → 'RUB'
        assert by_name['Vacation Home']['progress_percentage'] == pytest.approx(110.0)
        assert by_name['Vacation Home']['effective_currency'] == 'USD'

    def test_e2e_multiple_field_updates_same_session(self, db_session):
        """Multiple updates to the same field in one session should all be recorded."""
        asset = Asset(
            name="Multi-Update Asset",
            purchase_price=100000.0,
            current_value=100000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(asset)
        db_session.commit()

        # Three sequential updates in separate commits
        asset.current_value = 110000.0
        db_session.commit()
        asset.current_value = 120000.0
        db_session.commit()
        asset.current_value = 130000.0
        db_session.commit()

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).order_by(ValuationHistory.id).all()
        assert len(history) == 3
        assert history[0].old_value == 100000.0
        assert history[0].new_value == 110000.0
        assert history[1].old_value == 110000.0
        assert history[1].new_value == 120000.0
        assert history[2].old_value == 120000.0
        assert history[2].new_value == 130000.0

    def test_e2e_financial_goal_none_currency_effective_rub(self, db_session):
        """FinancialGoal with currency=None should return 'RUB' from effective_currency."""
        goal = FinancialGoal(
            name="Legacy Goal",
            target_amount=5000000.0,
            current_value=1000000.0,
            # currency column is NULL (pre-migration)
        )
        db_session.add(goal)
        db_session.commit()

        assert goal.effective_currency == 'RUB'
        assert goal.progress_percentage == 20.0

    def test_e2e_full_lifecycle_import_to_stale_to_update(self, db_session):
        """Full lifecycle: import data → detect stale → update value → verify history."""
        # Step 1: "Import" — add assets with old valuation dates (simulating Excel import)
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)
        assets = [
            Asset(name="Apartment", purchase_price=5000000.0, current_value=6000000.0,
                  valuation_date=old_date, category="real_estate", asset_type="foundation"),
            Asset(name="Stocks", purchase_price=2000000.0, current_value=2500000.0,
                  valuation_date=old_date, category="stocks", asset_type="growth"),
            Asset(name="Crypto", purchase_price=500000.0, current_value=300000.0,
                  valuation_date=old_date, category="crypto", asset_type="high_risk"),
        ]
        liabilities = [
            Liability(name="Mortgage", liability_type="mortgage", amount=4000000.0,
                      remaining_balance=3500000.0, valuation_date=old_date),
        ]
        db_session.add_all(assets + liabilities)
        db_session.commit()

        # Step 2: Check stale records (all should be stale)
        stale = get_stale_records(db_session)
        assert len(stale) == 4  # 3 assets + 1 liability

        # Step 3: User updates one asset (revaluation)
        apartment = db_session.query(Asset).filter_by(name="Apartment").first()
        apartment.current_value = 6500000.0
        apartment.record_valuation_change(db_session, 'current_value', change_reason='annual_revaluation')
        db_session.commit()

        # Step 4: Verify — stale records now 3 (apartment still stale by date, but has history)
        stale_after = get_stale_records(db_session)
        assert len(stale_after) == 4  # apartment is still stale by date (>90 days)

        # Step 5: Verify history was created
        history = db_session.query(ValuationHistory).filter_by(asset_id=apartment.id).all()
        assert len(history) == 1
        assert history[0].old_value == 6000000.0
        assert history[0].new_value == 6500000.0
        assert history[0].change_reason == 'annual_revaluation'

        # Step 6: Verify other assets have no history (not updated)
        stocks = db_session.query(Asset).filter_by(name="Stocks").first()
        stocks_history = db_session.query(ValuationHistory).filter_by(asset_id=stocks.id).all()
        assert len(stocks_history) == 0

    def test_e2e_valuation_history_onset_null_valuation_date(self, db_session):
        """Assets with valuation_date=None should be stale but still track valuation changes."""
        asset = Asset(
            name="Unvalued Asset",
            purchase_price=1000000.0,
            current_value=1200000.0,
            valuation_date=None,  # Never valued
        )
        db_session.add(asset)
        db_session.commit()

        # Should be stale
        assert asset.is_stale is True

        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['days_stale'] is None  # No date → no days_stale

        # But we can still record a valuation change
        asset.current_value = 1300000.0
        asset.record_valuation_change(db_session, 'current_value', change_reason='first_valuation')
        db_session.commit()

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).all()
        assert len(history) == 1
        assert history[0].old_value == 1200000.0
        assert history[0].new_value == 1300000.0

    def test_e2e_record_valuation_change_no_old_value_skips(self, db_session):
        """record_valuation_change should silently skip if _old_{field} is not set."""
        # Create an asset WITHOUT committing (so after_insert event doesn't fire)
        asset = Asset(
            name="Uncommitted Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=datetime.datetime.now(datetime.timezone.utc),
        )
        # Don't commit — after_insert event won't fire, so _old_current_value won't be set

        # Calling record_valuation_change should return without creating history
        asset.current_value = 120000.0
        asset.record_valuation_change(db_session, 'current_value', change_reason='test')

        history = db_session.query(ValuationHistory).filter_by(asset_id=asset.id).all()
        assert len(history) == 0
