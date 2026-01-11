from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from apps.banking.main_bank_system import Base

class CardMaster(Base):
    __tablename__ = 'card_master'

    card_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String(50), nullable=False) # 'character', 'skill', 'skin'
    rarity = Column(String(10), nullable=False) # 'UR', 'SSR', 'SR', 'R', 'N'
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Attributes (Element, Stats, etc.)
    # Example: {"element": "fire", "base_power": 100}
    attributes = Column(JSONB, nullable=True)
    
    # Effects (Passive bonuses)
    # Example: [{"target": "stock_fee", "value": -0.05, "type": "percent"}]
    effects = Column(JSONB, nullable=True)

    is_active = Column(Boolean, server_default=text('true'))
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    def __repr__(self):
        return f"<CardMaster(id={self.card_id}, name={self.name}, rarity={self.rarity})>"

class GachaMaster(Base):
    __tablename__ = 'gacha_master'

    gacha_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    banner_image_url = Column(String, nullable=True)
    
    cost_amount = Column(Numeric(18, 2), nullable=False)
    currency_type = Column(String(50), server_default=text("'JPY'")) # 'JPY', 'CHI', etc.
    
    is_active = Column(Boolean, server_default=text('true'))
    display_order = Column(Integer, server_default=text('0'))

    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # Relations
    items = relationship("GachaItem", back_populates="gacha", cascade="all, delete-orphan")

class GachaItem(Base):
    __tablename__ = 'gacha_items'

    id = Column(Integer, primary_key=True)
    gacha_id = Column(Integer, ForeignKey('gacha_master.gacha_id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('card_master.card_id', ondelete='CASCADE'), nullable=False)
    
    weight = Column(Integer, nullable=False, server_default=text('1'))
    is_pickup = Column(Boolean, server_default=text('false'))

    gacha = relationship("GachaMaster", back_populates="items")
    card = relationship("CardMaster")
