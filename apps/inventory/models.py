from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from apps.banking.main_bank_system import Base

class UserCollection(Base):
    __tablename__ = 'user_collections'

    collection_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    card_id = Column(Integer, ForeignKey('card_master.card_id'), nullable=False)
    
    quantity = Column(Integer, server_default=text('0'), nullable=False)
    
    obtained_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'))

    card = relationship("CardMaster")

class UserEquipment(Base):
    __tablename__ = 'user_equipment'

    equipment_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    
    # Slot definitions:
    # 'character': Main character slot
    # 'skill_1', 'skill_2', ...: Skill slots
    slot_type = Column(String(50), nullable=False) 
    
    card_id = Column(Integer, ForeignKey('card_master.card_id'), nullable=True)

    equipped_at = Column(DateTime(timezone=True), server_default=text('now()'))

    card = relationship("CardMaster")
