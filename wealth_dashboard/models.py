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
    def is_stale(self, max_days=90):
        """Returns True if valuation_date is None or older than max_days days.

        A record with no valuation date is treated as stale (unknown data is
        worse than stale data — the user can't make informed decisions).
        """
        if self.valuation_date is None:
            return True
        delta = datetime.datetime.utcnow() - self.valuation_date
        return delta.days > max_days


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
    def is_stale(self, max_days=90):
        """Returns True if valuation_date is None or older than max_days days.

        A record with no valuation date is treated as stale (unknown data is
        worse than stale data — the user can't make informed decisions).
        """
        if self.valuation_date is None:
            return True
        delta = datetime.datetime.utcnow() - self.valuation_date
        return delta.days > max_days


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
    currency = Column(String, default='RUB')
    description = Column(String, nullable=True)
    notes = Column(String, nullable=True)

# Create engine and session
engine = create_engine('sqlite:///wealth_dashboard.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
