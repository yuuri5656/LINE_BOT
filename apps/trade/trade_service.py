from apps.trade.models import TradeRequest, TradeItem
from apps.inventory.models import UserCollection
from apps.banking.api import banking_api
from apps.stock.models import SessionLocal
from apps.banking.main_bank_system import Account
from sqlalchemy import func
import datetime

class TradeService:
    @staticmethod
    def create_trade(sender_id: str, receiver_id: str, offered_items: list, requested_items: list):
        """
        offered_items/requested_items: list of dict {'type': 'card'|'currency', 'id': ..., 'amount': ...}
        """
        db = SessionLocal()
        try:
            # Validate ownership of offered items
            for item in offered_items:
                if item['type'] == 'card':
                    uc = db.query(UserCollection).filter_by(user_id=sender_id, card_id=item['id']).first()
                    if not uc or uc.quantity < item['amount']:
                        return False, "提供アイテムを持っていません"
                # TODO: Check currency balance? (Maybe delay check until execution or check now)
            
            trade = TradeRequest(sender_id=sender_id, receiver_id=receiver_id, status='pending')
            db.add(trade)
            db.flush() # get trade_id

            # Add items
            for item in offered_items:
                ti = TradeItem(
                    trade_id=trade.trade_id,
                    owner_id=sender_id,
                    item_type=item['type'],
                    card_id=item.get('id') if item['type'] == 'card' else None,
                    quantity=item.get('amount') if item['type'] == 'card' else None,
                    currency_type=item.get('currency') if item['type'] == 'currency' else None,
                    amount=item.get('amount') if item['type'] == 'currency' else None
                )
                db.add(ti)
            
            # For requested items, owner_id is receiver_id (they need to give it)
            # OR, are we doing "I give X, I want Y"? Yes.
            # So requested items are owned by receiver_id in the trade definition.
            for item in requested_items:
                ti = TradeItem(
                    trade_id=trade.trade_id,
                    owner_id=receiver_id,
                    item_type=item['type'],
                    card_id=item.get('id') if item['type'] == 'card' else None,
                    quantity=item.get('amount') if item['type'] == 'card' else None,
                    currency_type=item.get('currency') if item['type'] == 'currency' else None,
                    amount=item.get('amount') if item['type'] == 'currency' else None
                )
                db.add(ti)

            db.commit()
            return True, "トレードを申し込みました", trade.trade_id
        except Exception as e:
            db.rollback()
            return False, f"エラー: {e}", None
        finally:
            db.close()

    @staticmethod
    def accept_trade(trade_id: int, user_id: str):
        db = SessionLocal()
        try:
            trade = db.query(TradeRequest).filter_by(trade_id=trade_id).first()
            if not trade:
                return False, "トレードが見つかりません"
            if trade.status != 'pending':
                return False, "このトレードは既に終了しています"
            if trade.receiver_id and trade.receiver_id != user_id:
                return False, "あなた宛のトレードではありません"

            # Execute Trade
            # 1. Verify all items exist (for both sides)
            # 2. Transfer items
            
            items = db.query(TradeItem).filter_by(trade_id=trade_id).all()
            
            for item in items:
                source_user = item.owner_id
                # Target user is the OTHER party
                target_user = trade.receiver_id if source_user == trade.sender_id else trade.sender_id
                
                if item.item_type == 'card':
                    # Check source has card
                    uc_source = db.query(UserCollection).filter_by(user_id=source_user, card_id=item.card_id).first()
                    if not uc_source or uc_source.quantity < item.quantity:
                        return False, f"{source_user}がカードを持っていません"
                        
                    # Transfer
                    uc_source.quantity -= item.quantity
                    
                    # Add to target
                    uc_target = db.query(UserCollection).filter_by(user_id=target_user, card_id=item.card_id).first()
                    if uc_target:
                        uc_target.quantity += item.quantity
                    else:
                        uc_target = UserCollection(user_id=target_user, card_id=item.card_id, quantity=item.quantity)
                        db.add(uc_target)
                        
                elif item.item_type == 'currency':
                    # Using Banking API?
                    # Need to find accounts.
                    # This implies TradeService has permission to move money.
                    source_acc = db.query(Account).filter_by(user_id=source_user, status='active').first()
                    target_acc = db.query(Account).filter_by(user_id=target_user, status='active').first()
                    
                    if not source_acc: return False, f"{source_user}の口座がありません"
                    if not target_acc: return False, f"{target_user}の口座がありません"
                    
                    # Check balance
                    # Note: Need to check total if multiple currency items exist? (Skipping for now)
                    if source_acc.balance < item.amount:
                        return False, f"{source_user}の残高不足"

                    # Transfer
                    banking_api.transfer(
                        from_account_number=source_acc.account_number,
                        to_account_number=target_acc.account_number,
                        amount=float(item.amount),
                        currency='JPY',
                        description=f"トレード: {trade_id}"
                    )

            trade.status = 'completed'
            trade.updated_at = func.now()
            db.commit()
            return True, "トレードが成立しました"
        except Exception as e:
            db.rollback()
            return False, f"エラー: {e}"
        finally:
            db.close()

trade_service = TradeService()
