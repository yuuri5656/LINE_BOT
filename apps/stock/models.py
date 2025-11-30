"""
株式トレードシステム ORM定義

独立したモジュールとして、株式システム専用のデータベースモデルを定義
"""
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    String,
    Numeric,
    DateTime,
    Integer,
    create_engine,
    text,
)
import config

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


class StockSymbol(Base):
    """stock_symbols テーブルの ORM 定義

    株式銘柄マスタ
    """
    __tablename__ = 'stock_symbols'

    symbol_id = Column(Integer, primary_key=True)
    symbol_code = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False)
    initial_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False)
    volatility = Column(Numeric(5, 4), nullable=False)
    dividend_yield = Column(Numeric(5, 2), nullable=False)
    market_cap = Column(BigInteger, nullable=True)
    description = Column(String, nullable=True)
    is_tradable = Column(Integer, server_default=text('true'))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    price_history = relationship('StockPriceHistory', back_populates='symbol', cascade='all, delete-orphan')
    user_holdings = relationship('UserStockHolding', back_populates='symbol')
    ai_holdings = relationship('AITraderHolding', back_populates='symbol')
    transactions = relationship('StockTransaction', back_populates='symbol')
    ai_transactions = relationship('AITraderTransaction', back_populates='symbol')
    events = relationship('StockEvent', back_populates='symbol', cascade='all, delete-orphan')
    dividends = relationship('DividendPayment', back_populates='symbol')

    def __repr__(self):
        return f"<StockSymbol(symbol_id={self.symbol_id}, code={self.symbol_code}, name={self.name}, price={self.current_price})>"


class StockPriceHistory(Base):
    """stock_price_history テーブルの ORM 定義

    株価履歴
    """
    __tablename__ = 'stock_price_history'

    price_id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id', ondelete='CASCADE'), nullable=False)
    price = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    daily_high = Column(Integer, nullable=True)
    daily_low = Column(Integer, nullable=True)
    trend = Column(Numeric(8, 6), nullable=True)
    timestamp = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    symbol = relationship('StockSymbol', back_populates='price_history')

    def __repr__(self):
        return f"<StockPriceHistory(price_id={self.price_id}, symbol_id={self.symbol_id}, price={self.price}, timestamp={self.timestamp})>"


class StockAccount(Base):
    """stock_accounts テーブルの ORM 定義

    株式用口座
    """
    __tablename__ = 'stock_accounts'

    stock_account_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    linked_bank_account_id = Column(BigInteger, ForeignKey('accounts.account_id'), nullable=False)
    cash_balance = Column(Numeric(18, 2), server_default=text('0'), nullable=False)
    total_value = Column(Numeric(18, 2), server_default=text('0'))
    registered_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    last_traded_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, server_default=text('true'))

    # リレーション（外部キーのみ、Accountクラスへの参照は避ける）
    holdings = relationship('UserStockHolding', back_populates='stock_account')
    transactions = relationship('StockTransaction', back_populates='stock_account')
    dividends = relationship('DividendPayment', back_populates='stock_account')

    def __repr__(self):
        return f"<StockAccount(stock_account_id={self.stock_account_id}, user_id={self.user_id}, cash_balance={self.cash_balance})>"


class UserStockHolding(Base):
    """user_stock_holdings テーブルの ORM 定義

    ユーザー株式保有
    """
    __tablename__ = 'user_stock_holdings'

    holding_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric(18, 4), nullable=False)
    total_cost = Column(Numeric(18, 2), nullable=False)
    stock_account_id = Column(Integer, ForeignKey('stock_accounts.stock_account_id'), nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    symbol = relationship('StockSymbol', back_populates='user_holdings')
    stock_account = relationship('StockAccount', back_populates='holdings')

    def __repr__(self):
        return f"<UserStockHolding(holding_id={self.holding_id}, user_id={self.user_id}, symbol_id={self.symbol_id}, quantity={self.quantity})>"


class StockTransaction(Base):
    """stock_transactions テーブルの ORM 定義

    株式取引履歴
    """
    __tablename__ = 'stock_transactions'

    transaction_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id'), nullable=False)
    trade_type = Column(String(10), nullable=False)  # 'buy', 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(18, 4), nullable=False)
    total_amount = Column(Numeric(18, 2), nullable=False)
    fee = Column(Numeric(18, 2), server_default=text('0'))
    stock_account_id = Column(Integer, ForeignKey('stock_accounts.stock_account_id'), nullable=False)
    status = Column(String(50), server_default=text("'completed'"))
    executed_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    symbol = relationship('StockSymbol', back_populates='transactions')
    stock_account = relationship('StockAccount', back_populates='transactions')

    def __repr__(self):
        return f"<StockTransaction(transaction_id={self.transaction_id}, user_id={self.user_id}, trade_type={self.trade_type}, quantity={self.quantity})>"


class AITrader(Base):
    """ai_traders テーブルの ORM 定義

    AIトレーダー
    """
    __tablename__ = 'ai_traders'

    trader_id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    strategy = Column(String(50), nullable=False)
    risk_level = Column(String(50), nullable=False)
    cash = Column(Numeric(18, 2), nullable=False)
    patience = Column(Numeric(3, 2), nullable=True)
    greed = Column(Numeric(3, 2), nullable=True)
    fear = Column(Numeric(3, 2), nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    contrarian = Column(Numeric(3, 2), nullable=True)
    herd_mentality = Column(Numeric(3, 2), nullable=True)
    is_active = Column(Integer, server_default=text('true'))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    holdings = relationship('AITraderHolding', back_populates='trader')
    transactions = relationship('AITraderTransaction', back_populates='trader')

    def __repr__(self):
        return f"<AITrader(trader_id={self.trader_id}, name={self.name}, strategy={self.strategy})>"


class AITraderHolding(Base):
    """ai_trader_holdings テーブルの ORM 定義

    AIトレーダー保有株
    """
    __tablename__ = 'ai_trader_holdings'

    ai_holding_id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey('ai_traders.trader_id'), nullable=False)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    trader = relationship('AITrader', back_populates='holdings')
    symbol = relationship('StockSymbol', back_populates='ai_holdings')

    def __repr__(self):
        return f"<AITraderHolding(ai_holding_id={self.ai_holding_id}, trader_id={self.trader_id}, symbol_id={self.symbol_id}, quantity={self.quantity})>"


class AITraderTransaction(Base):
    """ai_trader_transactions テーブルの ORM 定義

    AIトレーダー取引履歴
    """
    __tablename__ = 'ai_trader_transactions'

    ai_transaction_id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey('ai_traders.trader_id'), nullable=False)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id'), nullable=False)
    trade_type = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(18, 4), nullable=False)
    executed_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    trader = relationship('AITrader', back_populates='transactions')
    symbol = relationship('StockSymbol', back_populates='ai_transactions')

    def __repr__(self):
        return f"<AITraderTransaction(ai_transaction_id={self.ai_transaction_id}, trader_id={self.trader_id}, trade_type={self.trade_type})>"


class StockEvent(Base):
    """stock_events テーブルの ORM 定義

    経済イベント
    """
    __tablename__ = 'stock_events'

    event_id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id', ondelete='CASCADE'), nullable=True)
    event_type = Column(String(50), nullable=False)
    event_text = Column(String, nullable=False)
    impact = Column(Numeric(6, 4), nullable=False)
    occurred_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    symbol = relationship('StockSymbol', back_populates='events')

    def __repr__(self):
        return f"<StockEvent(event_id={self.event_id}, event_type={self.event_type}, impact={self.impact})>"


class DividendPayment(Base):
    """dividend_payments テーブルの ORM 定義

    配当金支払い履歴
    """
    __tablename__ = 'dividend_payments'

    dividend_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.symbol_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    dividend_per_share = Column(Numeric(18, 4), nullable=False)
    total_dividend = Column(Numeric(18, 2), nullable=False)
    stock_account_id = Column(Integer, ForeignKey('stock_accounts.stock_account_id'), nullable=False)
    payment_date = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # リレーション
    symbol = relationship('StockSymbol', back_populates='dividends')
    stock_account = relationship('StockAccount', back_populates='dividends')

    def __repr__(self):
        return f"<DividendPayment(dividend_id={self.dividend_id}, user_id={self.user_id}, total_dividend={self.total_dividend})>"


# セッションファクトリ
SessionLocal = sessionmaker(bind=engine)


def get_stock_db():
    """株式システム用データベースセッションを取得するジェネレータ関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
