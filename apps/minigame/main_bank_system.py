from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import config
import psycopg2
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    String,
    Numeric,
    DateTime,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import Integer, CHAR
import datetime

# データベースに接続するためのエンジンを作成
engine = create_engine(config.DATABASE_URL)

Base = declarative_base()

# Postgres 側に既に定義されている enum 型を参照するために create_type=False を使用
account_status_enum = PG_ENUM('active', 'frozen', 'closed', name="account_status", create_type=False)
account_type_enum = PG_ENUM('ordinary', 'time', name="account_type", create_type=False)
transaction_type_enum = PG_ENUM('transfer', 'deposit', 'withdrawal', 'fee', 'interest', name="transaction_type", create_type=False)
transaction_status_enum = PG_ENUM('pending', 'completed', 'failed', 'reversed', name="transaction_status", create_type=False)
entry_type_enum = PG_ENUM('debit', 'credit', name="entry_type", create_type=False)


class Branch(Base):
    """branches テーブルの ORM 定義

    対応する DB カラム:
        branch_id integer PK
        code varchar(10) NOT NULL UNIQUE
        name text NOT NULL
        address text nullable
        created_at timestamptz DEFAULT now()
    """

    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # リレーション
    accounts = relationship("Account", back_populates="branch")

    def __repr__(self):
        return f"<Branch(branch_id={self.branch_id}, code={self.code}, name={self.name})>"


class Account(Base):
    """accounts テーブルの ORM 定義

    対応する DB カラム:
        account_id bigint PK
        user_id bigint NOT NULL
        account_number varchar(20) NOT NULL UNIQUE
        balance numeric(18,2) NOT NULL DEFAULT 0
        currency char(4) NOT NULL
        status account_status NOT NULL DEFAULT 'active'::account_status
        type account_type nullable
        branch_id integer FK nullable
        created_at timestamptz DEFAULT now()
        updated_at timestamptz DEFAULT now()
    """

    __tablename__ = "accounts"

    account_id = Column(BigInteger, primary_key=True)
    # DB のスキーマ上では user_id は text 型のため、モデルも文字列で扱う
    user_id = Column(String, nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    balance = Column(Numeric(18, 2), nullable=False, server_default=text('0'))
    currency = Column(CHAR(4), nullable=False)
    status = Column(account_status_enum, nullable=False, server_default=text("'active'::account_status"))
    type = Column(account_type_enum, nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.branch_id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=func.now())

    # リレーション
    branch = relationship("Branch", back_populates="accounts")
    transactions_from = relationship(
        "Transaction",
        back_populates="from_account",
        foreign_keys='Transaction.from_account_id',
    )
    transactions_to = relationship(
        "Transaction",
        back_populates="to_account",
        foreign_keys='Transaction.to_account_id',
    )
    entries = relationship("TransactionEntry", back_populates="account")

    def __repr__(self):
        return f"<Account(account_id={self.account_id}, account_number={self.account_number}, balance={self.balance})>"


class Transaction(Base):
    """transactions テーブルの ORM 定義

    対応する DB カラム:
        transaction_id bigint PK
        from_account_id bigint FK -> accounts.account_id
        to_account_id bigint FK -> accounts.account_id
        amount numeric(18,2) NOT NULL
        currency char(4) NOT NULL
        type transaction_type NOT NULL
        status transaction_status NOT NULL DEFAULT 'pending'::transaction_status
        executed_at timestamptz
        created_at timestamptz DEFAULT now()
    """

    __tablename__ = "transactions"

    transaction_id = Column(BigInteger, primary_key=True)
    from_account_id = Column(BigInteger, ForeignKey('accounts.account_id'), nullable=True)
    to_account_id = Column(BigInteger, ForeignKey('accounts.account_id'), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(CHAR(4), nullable=False)
    type = Column(transaction_type_enum, nullable=False)
    status = Column(transaction_status_enum, nullable=False, server_default=text("'pending'::transaction_status"))
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # リレーション
    from_account = relationship('Account', foreign_keys=[from_account_id], back_populates='transactions_from')
    to_account = relationship('Account', foreign_keys=[to_account_id], back_populates='transactions_to')
    entries = relationship('TransactionEntry', back_populates='transaction', cascade='all, delete')

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, from={self.from_account_id}, to={self.to_account_id}, amount={self.amount})>"


class TransactionEntry(Base):
    """transaction_entries テーブルの ORM 定義

    対応する DB カラム:
        entry_id bigint PK
        transaction_id bigint FK -> transactions.transaction_id ON DELETE CASCADE
        account_id bigint FK -> accounts.account_id
        entry_type entry_type NOT NULL
        amount numeric(18,2) NOT NULL
        created_at timestamptz DEFAULT now()
    """

    __tablename__ = 'transaction_entries'

    entry_id = Column(BigInteger, primary_key=True)
    transaction_id = Column(BigInteger, ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=True)
    account_id = Column(BigInteger, ForeignKey('accounts.account_id'), nullable=True)
    entry_type = Column(entry_type_enum, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # リレーション
    transaction = relationship('Transaction', back_populates='entries')
    account = relationship('Account', back_populates='entries')

    def __repr__(self):
        return f"<TransactionEntry(entry_id={self.entry_id}, transaction_id={self.transaction_id}, account_id={self.account_id}, amount={self.amount})>"


# セッションファクトリ（必要に応じて外部で利用）
SessionLocal = sessionmaker(bind=engine)
