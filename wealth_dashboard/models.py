from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    asset_type = Column(String)  # foundation, growth, high_risk
    category = Column(String)  # real_estate, crypto, stocks, etc.
    purchase_price = Column(Float)
    current_value = Column(Float)
    quantity = Column(Float, default=1)
    currency = Column(String, default='RUB')
    valuation_date = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def is_stale(self):
        """Returns True if valuation_date is None or older than 90 days.

        A record with no valuation date is treated as stale (unknown data is
        worse than stale data — the user can't make informed decisions).
        """
        if self.valuation_date is None:
            return True
        delta = datetime.datetime.utcnow() - self.valuation_date
        return delta.days > 90

    def record_valuation_change(self, session, field_name, change_reason=None):
        """Record a valuation change in ValuationHistory.

        Creates a new ValuationHistory row capturing the old and new values
        for the specified field. The old value is read from the _old_{field_name}
        attribute set by the after_insert event; the new value is the current
        value on the object.

        Clears ``_pending_history`` for this field so the after_flush handler
        does not create a duplicate record.
        """
        old_attr = f'_old_{field_name}'
        old_value = getattr(self, old_attr, None)
        if old_value is None:
            return
        new_value = getattr(self, field_name, None)
        history = ValuationHistory(
            asset_id=self.id,
            liability_id=None,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.datetime.utcnow(),
            change_reason=change_reason or 'manual',
        )
        session.add(history)
        # Mark this field as handled so before_update skips it
        if not hasattr(self, '_recorded_fields'):
            self._recorded_fields = set()
        self._recorded_fields.add(field_name)


class Liability(Base):
    __tablename__ = 'liabilities'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    liability_type = Column(String)  # mortgage, loan, credit
    amount = Column(Float)
    interest_rate = Column(Float, default=0)
    remaining_balance = Column(Float)
    currency = Column(String, default='RUB')
    valuation_date = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default={})

    @property
    def is_stale(self):
        """Returns True if valuation_date is None or older than 90 days.

        A record with no valuation date is treated as stale (unknown data is
        worse than stale data — the user can't make informed decisions).
        """
        if self.valuation_date is None:
            return True
        delta = datetime.datetime.utcnow() - self.valuation_date
        return delta.days > 90

    def record_valuation_change(self, session, field_name, change_reason=None):
        """Record a valuation change in ValuationHistory.

        Creates a new ValuationHistory row capturing the old and new values
        for the specified field. The old value is read from the _old_{field_name}
        attribute set by the after_insert event; the new value is the current
        value on the object.

        Clears ``_pending_history`` for this field so the after_flush handler
        does not create a duplicate record.
        """
        old_attr = f'_old_{field_name}'
        old_value = getattr(self, old_attr, None)
        if old_value is None:
            return
        new_value = getattr(self, field_name, None)
        history = ValuationHistory(
            asset_id=None,
            liability_id=self.id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.datetime.utcnow(),
            change_reason=change_reason or 'manual',
        )
        session.add(history)
        # Mark this field as handled so before_update skips it
        if not hasattr(self, '_recorded_fields'):
            self._recorded_fields = set()
        self._recorded_fields.add(field_name)


class Income(Base):
    __tablename__ = 'income'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    monthly_amount = Column(Float)
    is_passive = Column(Integer, default=0)  # 0=active, 1=passive
    currency = Column(String, default='RUB')

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    category = Column(String)
    monthly_amount = Column(Float)
    currency = Column(String, default='RUB')

class UserOverride(Base):
    __tablename__ = 'user_overrides'

    id = Column(Integer, primary_key=True)
    sheet_name = Column(String)
    original_name = Column(String)
    assigned_type = Column(String)
    assigned_category = Column(String)

class ValuationHistory(Base):
    __tablename__ = 'valuation_history'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)
    liability_id = Column(Integer, ForeignKey('liabilities.id'), nullable=True)
    field_name = Column(String)  # e.g., 'current_value', 'purchase_price'
    old_value = Column(Float)
    new_value = Column(Float)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    change_reason = Column(String, nullable=True)

class FinancialGoal(Base):
    __tablename__ = 'financial_goals'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    target_amount = Column(Float)
    target_date = Column(DateTime)
    currency = Column(String)
    current_value = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage. Returns 0 if target_amount is 0 or None."""
        if self.target_amount is None or self.target_amount == 0:
            return 0.0
        current = float(self.current_value or 0)
        target = float(self.target_amount)
        return (current / target) * 100

    @property
    def effective_currency(self) -> str:
        """Return 'RUB' when currency is None (pre-migration data handling).

        SQLite returns None for pre-existing rows where the column didn't exist.
        None != 'RUB' causes existing records to be treated as "unknown currency"
        instead of Russian ruble. This property normalizes that.
        """
        return self.currency if self.currency is not None else 'RUB'

# Create engine and session
engine = create_engine('sqlite:///wealth_dashboard.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_stale_records(session) -> list[dict]:
    """Return all stale assets and liabilities as UI-ready dicts.

    A record is stale when ``valuation_date`` is None or older than 90 days.

    Returns a list of dicts with keys:
        name, type, days_stale, last_value, edit_url
    """
    from datetime import datetime, timezone

    cutoff = datetime.utcnow()
    stale_items: list[dict] = []

    # Assets
    for asset in session.query(Asset).all():
        if not asset.is_stale:
            continue
        days_stale = 0
        if asset.valuation_date is not None:
            days_stale = (cutoff - asset.valuation_date).days
        stale_items.append({
            'name': asset.name or 'Unnamed asset',
            'type': asset.category or asset.asset_type or 'unknown',
            'days_stale': days_stale if days_stale > 0 else None,
            'last_value': asset.current_value,
            'edit_url': f'/edit/asset/{asset.id}',
        })

    # Liabilities
    for liab in session.query(Liability).all():
        if not liab.is_stale:
            continue
        days_stale = 0
        if liab.valuation_date is not None:
            days_stale = (cutoff - liab.valuation_date).days
        stale_items.append({
            'name': liab.name or 'Unnamed liability',
            'type': liab.liability_type or 'unknown',
            'days_stale': days_stale if days_stale > 0 else None,
            'last_value': liab.remaining_balance,
            'edit_url': f'/edit/liability/{liab.id}',
        })

    return stale_items


# =============================================================================
# Task Group 4a + 4b: SQLAlchemy event handlers for Asset and Liability
# =============================================================================

from sqlalchemy import event


# --- Task Group 4a: Asset events ---

@event.listens_for(Asset, 'before_update')
def asset_before_update(mapper, connection, target):
    """Detect valuation field changes and store history for after_flush."""
    tracked_fields = ['current_value', 'purchase_price']
    history_list = []
    for field_name in tracked_fields:
        old_value = getattr(target, f'_old_{field_name}', None)
        new_value = getattr(target, field_name, None)
        if old_value != new_value and old_value is not None:
            # Skip fields already handled by record_valuation_change()
            if hasattr(target, '_recorded_fields') and field_name in target._recorded_fields:
                continue
            history_list.append({
                'field_name': field_name,
                'old_value': old_value,
                'new_value': new_value,
            })
            setattr(target, f'_old_{field_name}', new_value)
    # Always accumulate — do NOT guard with hasattr, so multiple updates
    # to the same field in one session are all recorded.
    if not hasattr(target, '_pending_history'):
        target._pending_history = []
    target._pending_history.extend(history_list)


@event.listens_for(Asset, 'after_insert')
def asset_after_insert(mapper, connection, target):
    """Store old values after inserting a new Asset."""
    for field_name in ['current_value', 'purchase_price']:
        value = getattr(target, field_name, None)
        if value is not None:
            setattr(target, f'_old_{field_name}', value)


# --- Task Group 4b: Liability events ---

@event.listens_for(Liability, 'before_update')
def liability_before_update(mapper, connection, target):
    """Detect remaining_balance changes and store history for after_flush."""
    history_list = []
    old_value = getattr(target, '_old_remaining_balance', None)
    new_value = getattr(target, 'remaining_balance', None)
    if old_value != new_value and old_value is not None:
        # Skip fields already handled by record_valuation_change()
        if hasattr(target, '_recorded_fields') and 'remaining_balance' in target._recorded_fields:
            history_list = []
        else:
            history_list.append({
                'field_name': 'remaining_balance',
                'old_value': old_value,
                'new_value': new_value,
            })
            setattr(target, '_old_remaining_balance', new_value)
    # Always accumulate — do NOT guard with hasattr, so multiple updates
    # to remaining_balance in one session are all recorded.
    if not hasattr(target, '_pending_history'):
        target._pending_history = []
    target._pending_history.extend(history_list)


@event.listens_for(Liability, 'after_insert')
def liability_after_insert(mapper, connection, target):
    """Store old values after inserting a new Liability."""
    value = getattr(target, 'remaining_balance', None)
    if value is not None:
        setattr(target, '_old_remaining_balance', value)
        target._pending_history = [{
            'field_name': 'remaining_balance',
            'old_value': value,
            'new_value': value,
        }]  # Populate so after_flush creates ValuationHistory record


# --- Session-level after_flush: create ValuationHistory records ---

# Guard to prevent duplicate registration when module is reloaded
_registration_done = False

def register_valuation_history_events():
    """Register after_flush handler on Session CLASS so it fires for ALL sessions.

    Previously registered on SessionLocal (specific instance), which meant
    test sessions never fired the handler.  Class-level registration makes
    the handler fire on every Session — including those created by tests.
    """
    global _registration_done
    from sqlalchemy.orm.session import Session
    from sqlalchemy import event

    if _registration_done:
        return  # Already registered on the Session class
    _registration_done = True

    def create_valuation_history(session, context):
        """Create ValuationHistory records for Assets and Liabilities with _pending_history."""
        for obj in list(session.new) + list(session.dirty):
            if isinstance(obj, (Asset, Liability)) and hasattr(obj, '_pending_history'):
                for h in obj._pending_history:
                    history_record = ValuationHistory(
                        asset_id=obj.id if isinstance(obj, Asset) else None,
                        liability_id=obj.id if isinstance(obj, Liability) else None,
                        field_name=h['field_name'],
                        old_value=h['old_value'],
                        new_value=h['new_value'],
                        changed_at=datetime.datetime.utcnow(),
                        change_reason='auto_update',
                    )
                    session.add(history_record)
                delattr(obj, '_pending_history')

    event.listen(Session, 'after_flush', create_valuation_history)


# Register session-level after_flush handler at module load time (on Session class)
register_valuation_history_events()
