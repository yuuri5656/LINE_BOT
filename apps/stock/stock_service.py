"""
株式トレードサービス - 内部実装

外部から直接インポートせず、api.py経由で使用すること
"""
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
from datetime import datetime
from apps.stock.models import (
    SessionLocal,
    StockSymbol,
    StockAccount,
    UserStockHolding,
    StockTransaction,
    DividendPayment
)
from apps.banking.main_bank_system import Account
from apps.banking.api import banking_api
from apps.utilities.timezone_utils import now_jst

# 準備預金口座（株式決済用）
RESERVE_ACCOUNT_NUMBER = '7777777'
RESERVE_BRANCH_CODE = '001'


class StockService:
    """株式売買・保有管理サービス"""

    @staticmethod
    def create_stock_account(user_id: str, bank_account_id: int) -> Optional[Dict]:
        """
        株式口座を作成

        Args:
            user_id: ユーザーID
            bank_account_id: 連携する銀行口座ID

        Returns:
            作成された株式口座情報、失敗時はNone
        """
        db = SessionLocal()
        try:
            # 既存口座チェック（一度連携すると変更不可）
            existing = db.query(StockAccount).filter_by(user_id=user_id).first()
            if existing:
                raise ValueError("既に株式口座が登録されています。変更はできません。")

            # 銀行口座の存在確認
            bank_account = db.query(Account).filter_by(account_id=bank_account_id).first()
            if not bank_account:
                raise ValueError("指定された銀行口座が見つかりません")

            # 新規作成
            new_account = StockAccount(
                user_id=user_id,
                linked_bank_account_id=bank_account_id,
                cash_balance=Decimal('0'),
                total_value=Decimal('0'),
                is_active=True
            )
            db.add(new_account)
            db.commit()
            db.refresh(new_account)

            return {
                'stock_account_id': new_account.stock_account_id,
                'user_id': new_account.user_id,
                'cash_balance': float(new_account.cash_balance),
                'total_value': float(new_account.total_value),
                'registered_at': new_account.registered_at,
                'exists': False
            }
        except Exception as e:
            db.rollback()
            print(f"株式口座作成エラー: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_stock_account(user_id: str) -> Optional[Dict]:
        """株式口座情報を取得"""
        db = SessionLocal()
        try:
            account = db.query(StockAccount).filter_by(user_id=user_id, is_active=True).first()
            if not account:
                return None

            return {
                'stock_account_id': account.stock_account_id,
                'user_id': account.user_id,
                'linked_bank_account_id': account.linked_bank_account_id,
                'cash_balance': float(account.cash_balance),
                'total_value': float(account.total_value or 0),
                'registered_at': account.registered_at,
                'last_traded_at': account.last_traded_at
            }
        finally:
            db.close()

    @staticmethod
    def get_all_stocks() -> List[Dict]:
        """全銘柄情報を取得"""
        db = SessionLocal()
        try:
            from apps.stock.models import StockPriceHistory
            stocks = db.query(StockSymbol).filter_by(is_tradable=True).all()
            result = []
            for s in stocks:
                # 前日終値取得（2番目に新しい価格履歴）
                previous_prices = db.query(StockPriceHistory)\
                    .filter_by(symbol_id=s.symbol_id)\
                    .order_by(StockPriceHistory.timestamp.desc())\
                    .limit(2).all()

                previous_close = previous_prices[1].price if len(previous_prices) >= 2 else s.current_price
                change_rate = ((s.current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0

                result.append({
                    'symbol_id': s.symbol_id,
                    'symbol_code': s.symbol_code,
                    'name': s.name,
                    'sector': s.sector,
                    'current_price': s.current_price,
                    'previous_close': previous_close,
                    'change_rate': change_rate,
                    'volatility': float(s.volatility),
                    'dividend_yield': float(s.dividend_yield),
                    'market_cap': s.market_cap,
                    'description': s.description
                })
            return result
        finally:
            db.close()

    @staticmethod
    def get_stock_by_code(symbol_code: str) -> Optional[Dict]:
        """銘柄コードから銘柄情報を取得"""
        db = SessionLocal()
        try:
            from apps.stock.models import StockPriceHistory
            stock = db.query(StockSymbol).filter_by(symbol_code=symbol_code, is_tradable=True).first()
            if not stock:
                return None

            # 価格履歴から前日終値と高安値を取得
            latest_history = db.query(StockPriceHistory)\
                .filter_by(symbol_id=stock.symbol_id)\
                .order_by(StockPriceHistory.timestamp.desc())\
                .first()

            previous_prices = db.query(StockPriceHistory)\
                .filter_by(symbol_id=stock.symbol_id)\
                .order_by(StockPriceHistory.timestamp.desc())\
                .limit(2).all()

            previous_close = previous_prices[1].price if len(previous_prices) >= 2 else stock.current_price
            daily_high = latest_history.daily_high if latest_history else stock.current_price
            daily_low = latest_history.daily_low if latest_history else stock.current_price

            return {
                'symbol_id': stock.symbol_id,
                'symbol_code': stock.symbol_code,
                'name': stock.name,
                'sector': stock.sector,
                'current_price': stock.current_price,
                'previous_close': previous_close,
                'daily_high': daily_high,
                'daily_low': daily_low,
                'volatility': float(stock.volatility),
                'dividend_yield': float(stock.dividend_yield),
                'market_cap': stock.market_cap,
                'description': stock.description
            }
        finally:
            db.close()

    @staticmethod
    def get_user_holdings(user_id: str) -> List[Dict]:
        """ユーザーの保有株一覧を取得"""
        db = SessionLocal()
        try:
            holdings = db.query(UserStockHolding).filter_by(user_id=user_id).all()
            result = []
            for h in holdings:
                stock = db.query(StockSymbol).filter_by(symbol_id=h.symbol_id).first()
                if stock:
                    current_value = stock.current_price * h.quantity
                    profit_loss = current_value - float(h.total_cost)
                    profit_loss_rate = (profit_loss / float(h.total_cost)) * 100 if h.total_cost > 0 else 0

                    result.append({
                        'holding_id': h.holding_id,
                        'symbol_id': h.symbol_id,
                        'symbol_code': stock.symbol_code,
                        'name': stock.name,
                        'quantity': h.quantity,
                        'average_price': float(h.average_price),
                        'total_cost': float(h.total_cost),
                        'current_price': stock.current_price,
                        'current_value': current_value,
                        'profit_loss': profit_loss,
                        'profit_loss_rate': profit_loss_rate
                    })
            return result
        finally:
            db.close()

    @staticmethod
    def buy_stock(user_id: str, symbol_code: str, quantity: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        株式を購入

        Returns:
            (成功フラグ, メッセージ, 取引情報)
        """
        db = SessionLocal()
        try:
            # 株式口座取得
            stock_account = db.query(StockAccount).filter_by(user_id=user_id, is_active=True).first()
            if not stock_account:
                return False, "株式口座が登録されていません", None

            # 銘柄情報取得
            stock = db.query(StockSymbol).filter_by(symbol_code=symbol_code, is_tradable=True).first()
            if not stock:
                return False, "指定された銘柄が見つかりません", None

            # 必要金額計算
            total_amount = Decimal(str(stock.current_price * quantity))

            # 銀行口座取得
            bank_account = db.query(Account).filter_by(account_id=stock_account.linked_bank_account_id).first()
            if not bank_account:
                return False, "連携銀行口座が見つかりません", None

            if bank_account.balance < total_amount:
                return False, f"残高不足です（必要: ¥{total_amount:,}、残高: ¥{bank_account.balance:,}）", None

            # 準備預金口座へ振込（株式購入代金）
            description = f"株式購入 {stock.symbol_code} {quantity}株"
            try:
                banking_api.transfer(
                    from_account_number=bank_account.account_number,
                    to_account_number=RESERVE_ACCOUNT_NUMBER,
                    amount=float(total_amount),
                    currency='JPY',
                    description=description
                )
            except Exception as e:
                return False, f"決済処理に失敗しました: {str(e)}", None

            # 保有株更新または新規作成
            holding = db.query(UserStockHolding).filter_by(
                user_id=user_id,
                symbol_id=stock.symbol_id
            ).first()

            if holding:
                # 既存保有株を更新（平均取得単価を再計算）
                new_total_cost = float(holding.total_cost) + float(total_amount)
                new_quantity = holding.quantity + quantity
                new_average_price = new_total_cost / new_quantity

                holding.quantity = new_quantity
                holding.average_price = Decimal(str(new_average_price))
                holding.total_cost = Decimal(str(new_total_cost))
                holding.updated_at = now_jst()
            else:
                # 新規保有株作成
                holding = UserStockHolding(
                    user_id=user_id,
                    symbol_id=stock.symbol_id,
                    quantity=quantity,
                    average_price=Decimal(str(stock.current_price)),
                    total_cost=total_amount,
                    stock_account_id=stock_account.stock_account_id
                )
                db.add(holding)

            # 取引履歴記録
            transaction = StockTransaction(
                user_id=user_id,
                symbol_id=stock.symbol_id,
                trade_type='buy',
                quantity=quantity,
                price=Decimal(str(stock.current_price)),
                total_amount=total_amount,
                fee=Decimal('0'),
                stock_account_id=stock_account.stock_account_id,
                status='completed'
            )
            db.add(transaction)

            # 最終取引日時更新
            stock_account.last_traded_at = now_jst()

            db.commit()

            return True, "購入が完了しました", {
                'symbol_code': symbol_code,
                'name': stock.name,
                'quantity': quantity,
                'price': stock.current_price,
                'total_amount': float(total_amount),
                'transaction_id': transaction.transaction_id
            }
        except Exception as e:
            db.rollback()
            print(f"株式購入エラー: {e}")
            return False, f"購入処理中にエラーが発生しました: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def sell_stock(user_id: str, symbol_code: str, quantity: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        株式を売却

        Returns:
            (成功フラグ, メッセージ, 取引情報)
        """
        db = SessionLocal()
        try:
            # 株式口座取得
            stock_account = db.query(StockAccount).filter_by(user_id=user_id, is_active=True).first()
            if not stock_account:
                return False, "株式口座が登録されていません", None

            # 銘柄情報取得
            stock = db.query(StockSymbol).filter_by(symbol_code=symbol_code, is_tradable=True).first()
            if not stock:
                return False, "指定された銘柄が見つかりません", None

            # 保有株確認
            holding = db.query(UserStockHolding).filter_by(
                user_id=user_id,
                symbol_id=stock.symbol_id
            ).first()

            if not holding:
                return False, "この銘柄を保有していません", None

            if holding.quantity < quantity:
                return False, f"保有株数が不足しています（保有: {holding.quantity}株）", None

            # 売却金額計算
            total_amount = Decimal(str(stock.current_price * quantity))

            # 銀行口座取得
            bank_account = db.query(Account).filter_by(account_id=stock_account.linked_bank_account_id).first()
            if not bank_account:
                return False, "連携銀行口座が見つかりません", None

            # 準備預金口座から振込（株式売却代金）
            description = f"株式売却 {stock.symbol_code} {quantity}株"
            try:
                banking_api.transfer(
                    from_account_number=RESERVE_ACCOUNT_NUMBER,
                    to_account_number=bank_account.account_number,
                    amount=float(total_amount),
                    currency='JPY',
                    description=description
                )
            except Exception as e:
                return False, f"決済処理に失敗しました: {str(e)}", None

            # 保有株更新
            if holding.quantity == quantity:
                # 全売却
                db.delete(holding)
            else:
                # 一部売却
                sell_ratio = quantity / holding.quantity
                holding.quantity -= quantity
                holding.total_cost = Decimal(str(float(holding.total_cost) * (1 - sell_ratio)))
                holding.updated_at = now_jst()

            # 取引履歴記録
            transaction = StockTransaction(
                user_id=user_id,
                symbol_id=stock.symbol_id,
                trade_type='sell',
                quantity=quantity,
                price=Decimal(str(stock.current_price)),
                total_amount=total_amount,
                fee=Decimal('0'),
                stock_account_id=stock_account.stock_account_id,
                status='completed'
            )
            db.add(transaction)

            # 最終取引日時更新
            stock_account.last_traded_at = now_jst()

            db.commit()

            return True, "売却が完了しました", {
                'symbol_code': symbol_code,
                'name': stock.name,
                'quantity': quantity,
                'price': stock.current_price,
                'total_amount': float(total_amount),
                'transaction_id': transaction.transaction_id
            }
        except Exception as e:
            db.rollback()
            print(f"株式売却エラー: {e}")
            return False, f"売却処理中にエラーが発生しました: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_transaction_history(user_id: str, limit: int = 20) -> List[Dict]:
        """取引履歴を取得"""
        db = SessionLocal()
        try:
            transactions = db.query(StockTransaction).filter_by(user_id=user_id)\
                .order_by(StockTransaction.executed_at.desc())\
                .limit(limit).all()

            result = []
            for t in transactions:
                stock = db.query(StockSymbol).filter_by(symbol_id=t.symbol_id).first()
                if stock:
                    result.append({
                        'transaction_id': t.transaction_id,
                        'symbol_code': stock.symbol_code,
                        'name': stock.name,
                        'trade_type': t.trade_type,
                        'quantity': t.quantity,
                        'price': float(t.price),
                        'total_amount': float(t.total_amount),
                        'status': t.status,
                        'executed_at': t.executed_at
                    })
            return result
        finally:
            db.close()


# サービスインスタンス
stock_service = StockService()
