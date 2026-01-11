from apps.inventory.models import UserCollection, UserEquipment
from apps.gacha.models import CardMaster
from apps.stock.models import SessionLocal
from sqlalchemy import func
import json

class InventoryService:
    @staticmethod
    def add_item(user_id: str, card_id: int, quantity: int = 1):
        db = SessionLocal()
        try:
            collection = db.query(UserCollection).filter_by(user_id=user_id, card_id=card_id).first()
            if collection:
                collection.quantity += quantity
            else:
                collection = UserCollection(user_id=user_id, card_id=card_id, quantity=quantity)
                db.add(collection)
            db.commit()
            return collection
        finally:
            db.close()

    @staticmethod
    def get_inventory(user_id: str):
        db = SessionLocal()
        try:
            items = db.query(UserCollection, CardMaster)\
                .join(CardMaster, UserCollection.card_id == CardMaster.card_id)\
                .filter(UserCollection.user_id == user_id, UserCollection.quantity > 0)\
                .all()
            
            result = []
            for uc, cm in items:
                result.append({
                    'card_id': cm.card_id,
                    'name': cm.name,
                    'type': cm.type,
                    'rarity': cm.rarity,
                    'image_url': cm.image_url,
                    'attributes': cm.attributes,
                    'effects': cm.effects,
                    'quantity': uc.quantity
                })
            return result
        finally:
            db.close()

    @staticmethod
    def equip_item(user_id: str, slot_type: str, card_id: int):
        # Validation logic here (check if user owns item, check correct type for slot)
        db = SessionLocal()
        try:
            # Check ownership
            owned = db.query(UserCollection).filter_by(user_id=user_id, card_id=card_id).first()
            if not owned or owned.quantity < 1:
                return False, "持っていないアイテムです"
            
            # Check card type vs slot type compatibility
            card = db.query(CardMaster).filter_by(card_id=card_id).first()
            # Simple check: character slot needs character type
            if slot_type == 'character' and card.type != 'character':
                return False, "キャラクタースロットにはキャラクターしか装備できません"
            if slot_type.startswith('skill') and card.type != 'skill':
                return False, "スキルスロットにはスキルしか装備できません"
            
            # Equip
            eq = db.query(UserEquipment).filter_by(user_id=user_id, slot_type=slot_type).first()
            if eq:
                eq.card_id = card_id
            else:
                eq = UserEquipment(user_id=user_id, slot_type=slot_type, card_id=card_id)
                db.add(eq)
            
            db.commit()
            return True, "装備しました"
        finally:
            db.close()

    @staticmethod
    def get_active_effects(user_id: str):
        """
        Aggregate all passive effects from equipped items.
        Returns: Dict of effect types and values.
        Example: {'stock_fee_reduction': 0.15, 'str_bonus': 20}
        """
        db = SessionLocal()
        try:
            equipped = db.query(CardMaster)\
                .join(UserEquipment, CardMaster.card_id == UserEquipment.card_id)\
                .filter(UserEquipment.user_id == user_id)\
                .all()
            
            effects_agg = {}
            for card in equipped:
                if card.effects:
                    effects_list = card.effects if isinstance(card.effects, list) else []
                    for eff in effects_list:
                        target = eff.get('target')
                        val = eff.get('value', 0)
                        
                        # Simple summation for now.
                        # Could be more complex logic (multiplicative vs additive)
                        current_val = effects_agg.get(target, 0)
                        effects_agg[target] = current_val + val
            
            return effects_agg
        finally:
            db.close()

inventory_service = InventoryService()
