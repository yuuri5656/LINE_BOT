from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from apps.banking.main_bank_system import Base


class TaxProfile(Base):
    __tablename__ = 'tax_profiles'

    user_id = Column(String, primary_key=True)
    tax_account_id = Column(BigInteger, ForeignKey('accounts.account_id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))


class TaxPeriod(Base):
    __tablename__ = 'tax_periods'

    period_id = Column(BigInteger, primary_key=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))


class TaxIncomeEvent(Base):
    __tablename__ = 'tax_income_events'

    event_id = Column(BigInteger, primary_key=True)
    user_id = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    taxable_amount = Column(Numeric(18, 2), nullable=False, server_default=text('0'))
    source_type = Column(String, nullable=False)
    source_id = Column(BigInteger, nullable=False)
    meta_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))


class TaxAssessment(Base):
    __tablename__ = 'tax_assessments'

    assessment_id = Column(BigInteger, primary_key=True)
    user_id = Column(String, nullable=False)
    period_id = Column(BigInteger, ForeignKey('tax_periods.period_id', ondelete='CASCADE'), nullable=False)
    total_income = Column(Numeric(18, 2), nullable=False)
    taxable_income = Column(Numeric(18, 2), nullable=False)
    tax_amount = Column(Numeric(18, 2), nullable=False)
    status = Column(String, nullable=False)
    assessed_at = Column(DateTime(timezone=True), server_default=text('now()'))
    due_at = Column(DateTime(timezone=True), nullable=False)
    payment_window_end_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))

    period = relationship('TaxPeriod')


class TaxPayment(Base):
    __tablename__ = 'tax_payments'

    payment_id = Column(BigInteger, primary_key=True)
    assessment_id = Column(BigInteger, ForeignKey('tax_assessments.assessment_id', ondelete='CASCADE'), nullable=False)
    bank_transaction_id = Column(BigInteger, ForeignKey('transactions.transaction_id', ondelete='SET NULL'), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    assessment = relationship('TaxAssessment')
