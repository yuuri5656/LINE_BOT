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
# 接続プールの設定を追加してSSLエラーを回避
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,  # 接続を使う前に有効性を確認
    pool_recycle=3600,   # 1時間ごとに接続を再作成
    pool_size=5,         # 接続プールサイズ
    max_overflow=10      # 最大オーバーフロー接続数
)

Base = declarative_base()

# Postgres 側に既に定義されている enum 型を参照するために create_type=False を使用
account_status_enum = PG_ENUM('active', 'frozen', 'closed', name="account_status", create_type=False)
account_type_enum = PG_ENUM('ordinary', 'time', 'current', name="account_type", create_type=False)
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


class Customer(Base):
    """customers テーブルの ORM 定義

    対応する DB カラム:
        customer_id bigint PK
        full_name text NOT NULL
        date_of_birth date NOT NULL
        user_id text NOT NULL UNIQUE
        created_at timestamptz DEFAULT now()
        updated_at timestamptz DEFAULT now()
    """

    __tablename__ = "customers"

    customer_id = Column(BigInteger, primary_key=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=func.now())

    # リレーション
    accounts = relationship("Account", back_populates="customer")
    credentials = relationship("CustomerCredential", back_populates="customer", uselist=False, cascade="all, delete")

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id}, full_name={self.full_name}, user_id={self.user_id})>"


class CustomerCredential(Base):
    """customer_credentials テーブルの ORM 定義

    対応する DB カラム:
        customer_id bigint PK, FK -> customers.customer_id ON DELETE CASCADE
        pin_hash text NOT NULL
        pin_salt text NOT NULL
        created_at timestamptz DEFAULT now()
        updated_at timestamptz DEFAULT now()
    """

    __tablename__ = "customer_credentials"

    customer_id = Column(BigInteger, ForeignKey('customers.customer_id', ondelete='CASCADE'), primary_key=True)
    pin_hash = Column(String, nullable=False)
    pin_salt = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=func.now())

    # リレーション
    customer = relationship("Customer", back_populates="credentials")

    def __repr__(self):
        return f"<CustomerCredential(customer_id={self.customer_id})>"


class Account(Base):
    """accounts テーブルの ORM 定義

    対応する DB カラム:
        account_id bigint PK
        customer_id bigint FK -> customers.customer_id
        user_id text NOT NULL
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
    customer_id = Column(BigInteger, ForeignKey('customers.customer_id'), nullable=False)
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
    customer = relationship("Customer", back_populates="accounts")
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


class MinigameAccount(Base):
    """minigame_accounts テーブルの ORM 定義

    ユーザーがミニゲームで使用する口座を登録・管理するためのテーブル。
    1ユーザーにつき1つのミニゲーム口座のみ登録可能。

    対応する DB カラム:
        minigame_account_id serial PK
        user_id varchar(255) NOT NULL UNIQUE
        account_id integer FK -> accounts.account_id ON DELETE CASCADE
        registered_at timestamp DEFAULT now()
        last_used_at timestamp
        is_active boolean DEFAULT true
    """

    __tablename__ = 'minigame_accounts'

    minigame_account_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    account_id = Column(BigInteger, ForeignKey('accounts.account_id', ondelete='CASCADE'), unique=True, nullable=False)
    registered_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, server_default=text('true'))  # PostgreSQL boolean

    # リレーション
    account = relationship('Account')

    def __repr__(self):
        return f"<MinigameAccount(minigame_account_id={self.minigame_account_id}, user_id={self.user_id}, account_id={self.account_id}, is_active={self.is_active})>"


class MinigameChip(Base):
    """minigame_chips テーブルの ORM 定義

    ミニゲーム用チップ残高を管理
    """
    __tablename__ = 'minigame_chips'

    chip_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    balance = Column(Numeric(15, 2), server_default=text('0'), nullable=False)
    locked_balance = Column(Numeric(15, 2), server_default=text('0'), nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return f"<MinigameChip(chip_id={self.chip_id}, user_id={self.user_id}, balance={self.balance}, locked={self.locked_balance})>"


class ChipTransaction(Base):
    """chip_transactions テーブルの ORM 定義

    チップ取引履歴
    """
    __tablename__ = 'chip_transactions'

    transaction_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    type = Column(String(50), nullable=False)  # 'purchase', 'transfer_in', 'transfer_out', 'game_bet', 'game_win', 'game_refund'
    related_user_id = Column(String(255), nullable=True)
    game_session_id = Column(String(255), nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return f"<ChipTransaction(transaction_id={self.transaction_id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>"


class ShopPaymentAccount(Base):
    """shop_payment_accounts テーブルの ORM 定義

    ショップ支払い用口座登録
    """
    __tablename__ = 'shop_payment_accounts'

    payment_account_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    account_id = Column(BigInteger, ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False)
    registered_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, server_default=text('true'))

    # リレーション
    account = relationship('Account')

    def __repr__(self):
        return f"<ShopPaymentAccount(payment_account_id={self.payment_account_id}, user_id={self.user_id}, account_id={self.account_id})>"


class ShopItem(Base):
    """shop_items テーブルの ORM 定義

    ショップ商品マスタ
    """
    __tablename__ = 'shop_items'

    item_id = Column(Integer, primary_key=True)
    item_code = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(15, 2), nullable=False)
    stock = Column(Integer, server_default=text('-1'))
    is_available = Column(Integer, server_default=text('true'))
    display_order = Column(Integer, server_default=text('0'))
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    attributes = relationship('ShopItemAttribute', back_populates='item', cascade='all, delete-orphan')
    purchases = relationship('ShopPurchase', back_populates='item')

    def __repr__(self):
        return f"<ShopItem(item_id={self.item_id}, item_code={self.item_code}, name={self.name}, category={self.category})>"


class ShopItemAttribute(Base):
    """shop_item_attributes テーブルの ORM 定義

    商品属性（EAVパターン）
    """
    __tablename__ = 'shop_item_attributes'

    attribute_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('shop_items.item_id', ondelete='CASCADE'), nullable=False)
    attribute_key = Column(String(100), nullable=False)
    attribute_value = Column(String, nullable=False)
    attribute_type = Column(String(50), server_default=text("'string'"))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    item = relationship('ShopItem', back_populates='attributes')

    def __repr__(self):
        return f"<ShopItemAttribute(attribute_id={self.attribute_id}, item_id={self.item_id}, key={self.attribute_key}, value={self.attribute_value})>"


class ShopPurchase(Base):
    """shop_purchases テーブルの ORM 定義

    ショップ購入履歴
    """
    __tablename__ = 'shop_purchases'

    purchase_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    item_id = Column(Integer, ForeignKey('shop_items.item_id'), nullable=False)
    quantity = Column(Integer, server_default=text('1'))
    total_price = Column(Numeric(15, 2), nullable=False)
    payment_account_id = Column(BigInteger, ForeignKey('accounts.account_id'), nullable=True)
    status = Column(String(50), server_default=text("'completed'"))
    purchased_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    item = relationship('ShopItem', back_populates='purchases')
    payment_account = relationship('Account', foreign_keys=[payment_account_id])

    def __repr__(self):
        return f"<ShopPurchase(purchase_id={self.purchase_id}, user_id={self.user_id}, item_id={self.item_id}, status={self.status})>"


# セッションファクトリ（必要に応じて外部で利用）
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """データベースセッションを取得するジェネレータ関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
