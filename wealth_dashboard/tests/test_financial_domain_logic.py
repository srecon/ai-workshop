"""Tests for financial domain logic: is_stale property, get_stale_records,
ValuationHistory recording, FinancialGoal progress, and effective_currency."""

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

        # This should fail because is_stale property doesn't exist yet
        assert asset.is_stale is True

    def test_asset_is_stale_with_old_date(self, db_session):
        """An asset with valuation_date > 90 days ago should be considered stale."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=old_date,
        )
        db_session.add(asset)
        db_session.commit()

        # This should fail because is_stale property doesn't exist yet
        assert asset.is_stale is True

    def test_asset_is_not_stale_with_recent_date(self, db_session):
        """An asset with valuation_date < 90 days ago should NOT be considered stale."""
        recent_date = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
            valuation_date=recent_date,
        )
        db_session.add(asset)
        db_session.commit()

        # This should fail because is_stale property doesn't exist yet
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

        # This should fail because is_stale property doesn't exist yet
        assert liability.is_stale is True

    def test_liability_is_stale_with_old_date(self, db_session):
        """A liability with valuation_date > 90 days ago should be considered stale."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=95)
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=old_date,
        )
        db_session.add(liability)
        db_session.commit()

        # This should fail because is_stale property doesn't exist yet
        assert liability.is_stale is True

    def test_liability_is_not_stale_with_recent_date(self, db_session):
        """A liability with valuation_date < 90 days ago should NOT be considered stale."""
        recent_date = datetime.datetime.utcnow() - datetime.timedelta(days=10)
        liability = Liability(
            name="Test Loan",
            liability_type="loan",
            amount=500000.0,
            remaining_balance=400000.0,
            valuation_date=recent_date,
        )
        db_session.add(liability)
        db_session.commit()

        # This should fail because is_stale property doesn't exist yet
        assert liability.is_stale is False


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 2: get_stale_records helper
# =============================================================================


class TestGetStaleRecords:
    """Tests for the get_stale_records helper function."""

    def test_get_stale_records_returns_stale_assets_and_liabilities(self, db_session):
        """get_stale_records should return all stale assets and liabilities."""
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=100)
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
            valuation_date=datetime.datetime.utcnow(),
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

        # This should fail because get_stale_records function doesn't exist yet
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
            valuation_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
        )
        db_session.add(fresh_asset)
        db_session.commit()

        # This should fail because get_stale_records function doesn't exist yet
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

        # This should fail because get_stale_records function doesn't exist yet
        stale = get_stale_records(db_session)
        assert len(stale) == 1
        assert stale[0]['name'] == 'No Date Asset'


# =============================================================================
# Task Group 3a: Asset.record_valuation_change()
# =============================================================================


class TestRecordValuationChange:
    """Tests for the record_valuation_change method on Asset."""

    def test_asset_record_valuation_change_creates_history(self, db_session):
        """Calling record_valuation_change should create a ValuationHistory row."""
        asset = Asset(
            name="Test Asset",
            purchase_price=100000.0,
            current_value=110000.0,
        )
        db_session.add(asset)
        db_session.commit()

        # This should fail because record_valuation_change doesn't exist yet
        asset.record_valuation_change(
            db_session,
            field_name='current_value',
            change_reason='manual_update',
        )

        history = db_session.query(ValuationHistory).filter_by(
            asset_id=asset.id,
            field_name='current_value',
        ).one()
        assert history.old_value == 110000.0
        assert history.new_value == 110000.0  # no change, but still recorded
        assert history.change_reason == 'manual_update'

    def test_liability_record_valuation_change_creates_history(self, db_session):
        """Calling record_valuation_change on Liability should create a ValuationHistory row."""
        liability = Liability(
            name="Mortgage Loan",
            liability_type="mortgage",
            amount=5000000.0,
            remaining_balance=4500000.0,
        )
        db_session.add(liability)
        db_session.commit()

        # This should fail because Liability.record_valuation_change doesn't exist yet
        liability.record_valuation_change(
            db_session,
            field_name='remaining_balance',
            change_reason='payment_made',
        )

        history = db_session.query(ValuationHistory).filter_by(
            liability_id=liability.id,
            field_name='remaining_balance',
        ).one()
        assert history.old_value == 4500000.0
        assert history.new_value == 4500000.0  # no change, but still recorded
        assert history.asset_id is None
        assert history.change_reason == 'payment_made'
