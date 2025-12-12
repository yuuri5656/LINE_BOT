"""
懲役システム用の SQLAlchemy ORM モデル定義
"""
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    text,
)
from apps.banking.main_bank_system import Base

class PrisonSentence(Base):
    """
    懲役情報テーブル (prison_sentences)
    
    対応する DB カラム:
        sentence_id SERIAL PRIMARY KEY
        user_id TEXT NOT NULL UNIQUE
        customer_id BIGINT NOT NULL -> customers.customer_id
        start_date DATE NOT NULL          -- 施行日
        end_date DATE NOT NULL            -- 釈放日
        initial_days INTEGER NOT NULL     -- 初期懲役日数
        remaining_days INTEGER NOT NULL   -- 残り懲役日数
        daily_quota INTEGER NOT NULL      -- 1日のノルマ（?労働回数）
        completed_today INTEGER           -- 今日の?労働実行回数
        last_work_date DATE               -- 最後に?労働を実行した日付
        created_at TIMESTAMPTZ DEFAULT now()
        updated_at TIMESTAMPTZ DEFAULT now()
    """
    
    __tablename__ = "prison_sentences"
    
    sentence_id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='CASCADE'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_days = Column(Integer, nullable=False)
    remaining_days = Column(Integer, nullable=False)
    daily_quota = Column(Integer, nullable=False)
    completed_today = Column(Integer, default=0)
    last_work_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    def __repr__(self):
        return f"<PrisonSentence(user_id={self.user_id}, remaining_days={self.remaining_days}, end_date={self.end_date})>"


class PrisonRehabilitationFund(Base):
    """
    犯罪者更生給付金口座テーブル (prison_rehabilitation_fund)
    
    対応する DB カラム:
        fund_id SERIAL PRIMARY KEY
        account_id INTEGER NOT NULL UNIQUE -> accounts.account_id
        total_collected NUMERIC(15,2) DEFAULT 0  -- 累計収集額
        last_distribution_date DATE               -- 最後に分配した日付
        created_at TIMESTAMPTZ DEFAULT now()
        updated_at TIMESTAMPTZ DEFAULT now()
    """
    
    __tablename__ = "prison_rehabilitation_fund"
    
    fund_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False, unique=True)
    total_collected = Column(Numeric(15, 2), default=0)
    last_distribution_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    def __repr__(self):
        return f"<PrisonRehabilitationFund(account_id={self.account_id}, total_collected={self.total_collected})>"


class PrisonRehabilitationDistribution(Base):
    """
    給付金分配履歴テーブル (prison_rehabilitation_distributions)
    
    対応する DB カラム:
        distribution_id SERIAL PRIMARY KEY
        distribution_date DATE NOT NULL
        total_amount NUMERIC(15,2) NOT NULL
        recipient_count INTEGER NOT NULL
        amount_per_recipient NUMERIC(15,2) NOT NULL
        created_at TIMESTAMPTZ DEFAULT now()
    """
    
    __tablename__ = "prison_rehabilitation_distributions"
    
    distribution_id = Column(Integer, primary_key=True)
    distribution_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    recipient_count = Column(Integer, nullable=False)
    amount_per_recipient = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    
    def __repr__(self):
        return f"<PrisonRehabilitationDistribution(distribution_date={self.distribution_date}, total_amount={self.total_amount}, recipient_count={self.recipient_count})>"
