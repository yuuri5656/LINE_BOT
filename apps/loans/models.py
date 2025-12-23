from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, ForeignKey, text
from sqlalchemy.orm import relationship

from apps.banking.main_bank_system import Base


class Loan(Base):
    __tablename__ = 'loans'

    loan_id = Column(BigInteger, primary_key=True)
    user_id = Column(String, nullable=False)
    principal = Column(Numeric(18, 2), nullable=False)
    outstanding_balance = Column(Numeric(18, 2), nullable=False)
    status = Column(String, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=text('now()'))

    interest_weekly_rate = Column(Numeric(10, 6), nullable=False)
    interest_weekly_rate_cap_applied = Column(Numeric(10, 6), nullable=False)
    late_interest_weekly_rate = Column(Numeric(10, 6), nullable=False, server_default=text('0.200000'))

    autopay_account_id = Column(BigInteger, ForeignKey('accounts.account_id', ondelete='SET NULL'), nullable=True)
    autopay_amount = Column(Numeric(18, 2), nullable=False, server_default=text('1000'))

    last_autopay_attempt_at = Column(DateTime(timezone=True), nullable=True)
    autopay_failed_since = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))


class LoanPayment(Base):
    __tablename__ = 'loan_payments'

    payment_id = Column(BigInteger, primary_key=True)
    loan_id = Column(BigInteger, ForeignKey('loans.loan_id', ondelete='CASCADE'), nullable=False)
    bank_transaction_id = Column(BigInteger, ForeignKey('transactions.transaction_id', ondelete='SET NULL'), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    paid_at = Column(DateTime(timezone=True), server_default=text('now()'))
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    loan = relationship('Loan')
