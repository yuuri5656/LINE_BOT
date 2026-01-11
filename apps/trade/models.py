from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, ForeignKey, Numeric, text
from sqlalchemy.orm import relationship
from apps.banking.main_bank_system import Base

class TradeRequest(Base):
    __tablename__ = 'trade_requests'

    trade_id = Column(Integer, primary_key=True)
    sender_id = Column(String(255), nullable=False)
    receiver_id = Column(String(255), nullable=True) # None means public trade? (Optional future feature)
    
    status = Column(String(50), server_default=text("'pending'")) # 'pending', 'completed', 'cancelled', 'rejected'
    
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))

    items = relationship("TradeItem", back_populates="trade", cascade="all, delete-orphan")

class TradeItem(Base):
    __tablename__ = 'trade_items'

    item_id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trade_requests.trade_id', ondelete='CASCADE'), nullable=False)
    
    owner_id = Column(String(255), nullable=False) # Who is offering this item (Sender or Receiver?)
    # For now, let's assume sender offers items and requests nothing specific, OR negotiation?
    # Simpler model: Sender offers X, Y, Z. Receiver accepts.
    # To support "I give X for Y", we need to know who gives what.
    # owner_id = sender_id -> Sender gives this.
    
    item_type = Column(String(50), nullable=False) # 'card', 'currency'
    
    # If card
    card_id = Column(Integer, ForeignKey('card_master.card_id'), nullable=True)
    quantity = Column(Integer, nullable=True)
    
    # If currency
    currency_type = Column(String(50), nullable=True) # 'JPY'
    amount = Column(Numeric(18, 2), nullable=True)

    trade = relationship("TradeRequest", back_populates="items")
    card = relationship("CardMaster")
