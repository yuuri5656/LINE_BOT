from apps.gacha.models import GachaMaster, GachaItem, CardMaster
from apps.inventory.inventory_service import inventory_service
from apps.banking.api import banking_api
from apps.stock.models import SessionLocal
import random

class GachaService:
    @staticmethod
    def draw_gacha(user_id: str, gacha_id: int, count: int = 1):
        db = SessionLocal()
        try:
            gacha = db.query(GachaMaster).filter_by(gacha_id=gacha_id, is_active=True).first()
            if not gacha:
                return False, "ガチャが見つかりません", []

            # Calculate total cost
            total_cost = float(gacha.cost_amount) * count
            
            # Payment (Assumes JPY for now. Future: Support Chip)
            # Find linked bank account... this is tricky without account_id.
            # Using StockService to find linked account, or assume Main Account?
            # Creating a helper to find user's main active account.
            from apps.banking.main_bank_system import Account
            # Simplification: Find first active account for user
            account = db.query(Account).filter_by(user_id=user_id, status='active').first()
            if not account:
                return False, "支払い可能な銀行口座がありません", []
            
            if float(account.balance) < total_cost:
                return False, "残高不足です", []
            
            # Execute Payment
            try:
                banking_api.transfer(
                    from_account_number=account.account_number,
                    to_account_number='7777777', # Reserve Account
                    amount=total_cost,
                    currency='JPY',
                    description=f"ガチャ: {gacha.name} x{count}"
                )
            except Exception as e:
                return False, f"支払い失敗: {e}", []

            # Draw Logic
            items = db.query(GachaItem).filter_by(gacha_id=gacha_id).all()
            if not items:
                return False, "ガチャの中身が空です", []
            
            weights = [item.weight for item in items]
            drawn_items_data = []

            for _ in range(count):
                winner = random.choices(items, weights=weights, k=1)[0]
                
                # Add to inventory
                inventory_service.add_item(user_id, winner.card_id)
                
                # Fetch card details for result
                card = db.query(CardMaster).filter_by(card_id=winner.card_id).first()
                drawn_items_data.append({
                    'card_id': card.card_id,
                    'name': card.name,
                    'rarity': card.rarity,
                    'image_url': card.image_url,
                    'is_new': False # TODO: check if new
                })
            
            return True, "ガチャを引きました！", drawn_items_data

        except Exception as e:
            return False, f"エラー: {e}", []
        finally:
            db.close()
    
    @staticmethod
    def get_gacha_list():
        db = SessionLocal()
        try:
            gachas = db.query(GachaMaster).filter_by(is_active=True).order_by(GachaMaster.display_order).all()
            return [{
                'gacha_id': g.gacha_id,
                'name': g.name,
                'description': g.description,
                'cost': float(g.cost_amount),
                'currency': g.currency_type,
                'image_url': g.banner_image_url
            } for g in gachas]
        finally:
            db.close()

gacha_service = GachaService()
