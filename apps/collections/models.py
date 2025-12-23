from sqlalchemy import Column, BigInteger, Integer, String, Date, DateTime, Numeric, Boolean, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from apps.banking.main_bank_system import Base


class CreditProfile(Base):
    __tablename__ = 'credit_profile'

    user_id = Column(String, primary_key=True)
    is_blacklisted = Column(Boolean, nullable=False, server_default=text('false'))
    blacklisted_at = Column(DateTime(timezone=True), nullable=True)
    blacklisted_reason = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))


class CollectionsCase(Base):
    __tablename__ = 'collections_cases'

    case_id = Column(BigInteger, primary_key=True)
    user_id = Column(String, nullable=False)
    case_type = Column(String, nullable=False)
    reference_id = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    payment_window_end_at = Column(DateTime(timezone=True), nullable=True)
    overdue_started_at = Column(DateTime(timezone=True), nullable=True)
    blacklisted_at = Column(DateTime(timezone=True), nullable=True)
    seizure_started_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    last_inline_notice_at = Column(DateTime(timezone=True), nullable=True)
    last_push_notice_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, server_default=text('0'))
    push_notice_count = Column(Integer, nullable=False, server_default=text('0'))
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))


class CollectionsAccrual(Base):
    __tablename__ = 'collections_accruals'

    accrual_id = Column(BigInteger, primary_key=True)
    case_id = Column(BigInteger, ForeignKey('collections_cases.case_id', ondelete='CASCADE'), nullable=False)
    accrual_type = Column(String, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    principal_base = Column(Numeric(18, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    case = relationship('CollectionsCase')


class CollectionsEvent(Base):
    __tablename__ = 'collections_events'

    event_id = Column(BigInteger, primary_key=True)
    case_id = Column(BigInteger, ForeignKey('collections_cases.case_id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String, nullable=False)
    note = Column(String, nullable=True)
    meta_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    case = relationship('CollectionsCase')
