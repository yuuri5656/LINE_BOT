"""
株価変動サービス - AIトレーダー・イベントシステム・配当金処理

外部から直接インポートせず、api.py経由で使用すること
"""
import random
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
from apps.utilities.timezone_utils import now_jst
from apps.stock.models import (
    SessionLocal,
    StockSymbol,
    StockPriceHistory,
    AITrader,
    AITraderHolding,
    AITraderTransaction,
    StockEvent,
    DividendPayment,
    UserStockHolding,
    StockAccount
)
from apps.banking.api import banking_api
from apps.banking.main_bank_system import Account, SessionLocal as BankingSessionLocal


class TradingStrategy(Enum):
    """取引戦略"""
    MOMENTUM = "momentum"
    REVERSAL = "reversal"
    VALUE = "value"
    SCALPING = "scalping"
    RANDOM = "random"
    GROWTH = "growth"
    DAY_TRADER = "day_trader"
    SWING = "swing"
    LONG_TERM = "long_term"


class RiskLevel(Enum):
    """リスクレベル"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


class PriceService:
    """株価変動管理サービス"""

    # イベントデータ
    EVENTS = [
        {"text": "📈 新製品発表で好感", "impact": 0.15, "type": "product_launch"},
        {"text": "📉 不祥事が発覚", "impact": -0.20, "type": "scandal"},
        {"text": "💰 業績予想を上方修正", "impact": 0.12, "type": "earnings"},
        {"text": "⚠️ リコール発表", "impact": -0.15, "type": "scandal"},
        {"text": "🌐 海外展開を発表", "impact": 0.10, "type": "news"},
        {"text": "😰 大口株主が売却", "impact": -0.12, "type": "news"},
        {"text": "🎉 大型契約を獲得", "impact": 0.18, "type": "news"},
        {"text": "📊 決算発表：予想超え", "impact": 0.20, "type": "earnings"},
        {"text": "📊 決算発表：予想下回る", "impact": -0.18, "type": "earnings"},
        {"text": "🏆 業界トップのシェア獲得", "impact": 0.13, "type": "news"},
    ]

    @staticmethod
    def update_all_prices():
        """全銘柄の価格を更新"""
        db = SessionLocal()
        try:
            stocks = db.query(StockSymbol).filter_by(is_tradable=True).all()

            for stock in stocks:
                # AIトレーダーの売買集計
                buy_volume, sell_volume = PriceService._get_ai_trading_volume(db, stock.symbol_id)

                # イベント発生チェック（2%の確率）
                event_impact = 0
                if random.random() < 0.02:
                    event = random.choice(PriceService.EVENTS)
                    event_impact = event['impact']

                    # イベント記録
                    stock_event = StockEvent(
                        symbol_id=stock.symbol_id,
                        event_type=event['type'],
                        event_text=event['text'],
                        impact=Decimal(str(event_impact))
                    )
                    db.add(stock_event)

                # 価格更新
                new_price = PriceService._calculate_new_price(
                    stock,
                    buy_volume,
                    sell_volume,
                    event_impact
                )

                # 価格履歴に記録
                history = StockPriceHistory(
                    symbol_id=stock.symbol_id,
                    price=new_price,
                    volume=buy_volume + sell_volume,
                    daily_high=new_price,
                    daily_low=new_price,
                    trend=Decimal('0')
                )
                db.add(history)

                # 価格を更新
                stock.current_price = new_price
                stock.updated_at = now_jst()

            db.commit()
            print(f"[株価更新] {len(stocks)}銘柄の価格を更新しました")
        except Exception as e:
            import traceback
            db.rollback()
            print(f"株価更新エラー: {e}")
            print(f"エラー詳細:\n{traceback.format_exc()}")
        finally:
            db.close()

    @staticmethod
    def _calculate_new_price(stock: StockSymbol, buy_volume: int, sell_volume: int, event_impact: float) -> int:
        """新しい株価を計算"""
        current_price = stock.current_price

        # 1. ベースノイズ（小さなランダム変動）
        base_volatility = 0.005  # 0.5%
        base_change = random.gauss(0, base_volatility)

        # 2. 取引の影響
        total_volume = buy_volume + sell_volume
        if total_volume > 0:
            net_volume = buy_volume - sell_volume
            trade_impact = (net_volume / total_volume) * 0.03
            # 流動性調整
            liquidity_factor = 1.0 / (1.0 + total_volume / 10000)
            trade_impact *= liquidity_factor
        else:
            trade_impact = 0

        # 3. イベント影響
        total_change = base_change + trade_impact + event_impact

        # 4. 銘柄固有のボラティリティを適用
        volatility_factor = float(stock.volatility) / 0.03  # 基準3%
        total_change *= volatility_factor

        # ストップ高・ストップ安（±30%）
        total_change = max(-0.30, min(0.30, total_change))

        new_price = round(current_price * (1 + total_change))
        return max(1, new_price)  # 最低1円

    @staticmethod
    def _get_ai_trading_volume(db, symbol_id: int) -> tuple:
        """AIトレーダーの売買出来高を集計（簡易版）"""
        # 実際のAI取引ロジックは後で実装
        # 今はランダムな売買量を返す
        buy_volume = random.randint(100, 5000)
        sell_volume = random.randint(100, 5000)
        return buy_volume, sell_volume

    @staticmethod
    def execute_ai_trading():
        """AIトレーダーの取引を実行"""
        db = SessionLocal()
        try:
            traders = db.query(AITrader).filter_by(is_active=True).all()
            stocks = db.query(StockSymbol).filter_by(is_tradable=True).all()

            for trader in traders:
                # 各AIトレーダーがランダムに1-2銘柄を取引
                num_trades = random.randint(0, 2)
                selected_stocks = random.sample(stocks, min(num_trades, len(stocks)))

                for stock in selected_stocks:
                    decision = PriceService._ai_trade_decision(db, trader, stock)
                    if decision['action'] != 'hold':
                        PriceService._execute_ai_trade(db, trader, stock, decision)

            db.commit()
            print(f"[AI取引] {len(traders)}体のトレーダーが取引を実行しました")
        except Exception as e:
            import traceback
            db.rollback()
            print(f"AI取引エラー: {e}")
            print(f"エラー詳細:\n{traceback.format_exc()}")
        finally:
            db.close()

    @staticmethod
    def _ai_trade_decision(db, trader: AITrader, stock: StockSymbol) -> Dict:
        """AIトレーダーの取引判断（簡易版）"""
        strategy = TradingStrategy(trader.strategy)
        risk_level = RiskLevel(trader.risk_level)

        # 戦略ごとの判断（簡易実装）
        if strategy == TradingStrategy.MOMENTUM:
            # 順張り：価格が上昇傾向なら買い
            if random.random() < 0.4:
                return {'action': 'buy', 'quantity': random.randint(10, 100)}
            elif random.random() < 0.2:
                return {'action': 'sell', 'quantity': random.randint(10, 50)}

        elif strategy == TradingStrategy.REVERSAL:
            # 逆張り：価格が下落なら買い
            if random.random() < 0.3:
                return {'action': 'buy', 'quantity': random.randint(10, 80)}
            elif random.random() < 0.3:
                return {'action': 'sell', 'quantity': random.randint(10, 80)}

        elif strategy == TradingStrategy.RANDOM:
            # ランダム
            action = random.choice(['buy', 'sell', 'hold', 'hold'])
            if action != 'hold':
                return {'action': action, 'quantity': random.randint(5, 50)}

        return {'action': 'hold', 'quantity': 0}

    @staticmethod
    def _execute_ai_trade(db, trader: AITrader, stock: StockSymbol, decision: Dict):
        """AIトレーダーの取引を実行"""
        try:
            quantity = decision['quantity']
            action = decision['action']

            if action == 'buy':
                # 購入処理
                cost = stock.current_price * quantity
                if trader.cash >= cost:
                    trader.cash = Decimal(str(float(trader.cash) - cost))

                    # 保有株更新
                    holding = db.query(AITraderHolding).filter_by(
                        trader_id=trader.trader_id,
                        symbol_id=stock.symbol_id
                    ).first()

                    if holding:
                        new_total = float(holding.average_price) * holding.quantity + cost
                        holding.quantity += quantity
                        holding.average_price = Decimal(str(new_total / holding.quantity))
                        holding.updated_at = now_jst()
                    else:
                        holding = AITraderHolding(
                            trader_id=trader.trader_id,
                            symbol_id=stock.symbol_id,
                            quantity=quantity,
                            average_price=Decimal(str(stock.current_price))
                        )
                        db.add(holding)

                    # 取引履歴
                    tx = AITraderTransaction(
                        trader_id=trader.trader_id,
                        symbol_id=stock.symbol_id,
                        trade_type='buy',
                        quantity=quantity,
                        price=Decimal(str(stock.current_price))
                    )
                    db.add(tx)

            elif action == 'sell':
                # 売却処理
                holding = db.query(AITraderHolding).filter_by(
                    trader_id=trader.trader_id,
                    symbol_id=stock.symbol_id
                ).first()

                if holding and holding.quantity >= quantity:
                    proceeds = stock.current_price * quantity
                    trader.cash = Decimal(str(float(trader.cash) + proceeds))

                    if holding.quantity == quantity:
                        db.delete(holding)
                    else:
                        holding.quantity -= quantity
                        holding.updated_at = now_jst()

                    # 取引履歴
                    tx = AITraderTransaction(
                        trader_id=trader.trader_id,
                        symbol_id=stock.symbol_id,
                        trade_type='sell',
                        quantity=quantity,
                        price=Decimal(str(stock.current_price))
                    )
                    db.add(tx)

        except Exception as e:
            print(f"AI取引実行エラー ({trader.name}): {e}")

    @staticmethod
    def pay_dividends():
        """配当金を支払い（1日1回、午前8時前後）"""
        db = SessionLocal()
        bank_db = BankingSessionLocal()
        try:
            # 全保有株を取得
            holdings = db.query(UserStockHolding).all()
            total_paid = 0
            success_count = 0
            fail_count = 0

            for holding in holdings:
                try:
                    stock = db.query(StockSymbol).filter_by(symbol_id=holding.symbol_id).first()
                    if not stock or stock.dividend_yield <= 0:
                        continue

                    # 配当金計算（年間配当利回りの1/4）
                    annual_dividend = stock.current_price * (float(stock.dividend_yield) / 100)
                    quarterly_dividend = annual_dividend / 4
                    dividend_per_share = Decimal(str(quarterly_dividend))
                    total_dividend = dividend_per_share * holding.quantity

                    if total_dividend <= 0:
                        continue

                    # 株式口座から連携銀行口座を取得
                    stock_account = db.query(StockAccount).filter_by(
                        stock_account_id=holding.stock_account_id
                    ).first()

                    if not stock_account:
                        print(f"[配当金] 株式口座が見つかりません (user_id={holding.user_id})")
                        fail_count += 1
                        continue

                    # 銀行口座情報を取得
                    bank_account = bank_db.query(Account).filter_by(
                        account_id=stock_account.linked_bank_account_id
                    ).first()

                    if not bank_account or not bank_account.branch:
                        print(f"[配当金] 連携銀行口座が見つかりません (user_id={holding.user_id})")
                        fail_count += 1
                        continue

                    # ステータスチェック: activeまたはfrozenのみ有効
                    if bank_account.status not in ('active', 'frozen'):
                        print(f"[配当金] 連携銀行口座が利用できません (user_id={holding.user_id}, status={bank_account.status})")
                        fail_count += 1
                        continue

                    # 準備預金口座から振込（配当金）
                    from apps.stock.stock_service import RESERVE_ACCOUNT_NUMBER
                    description = f"配当金 {stock.symbol_code} {holding.quantity}株"
                    try:
                        banking_api.transfer(
                            from_account_number=RESERVE_ACCOUNT_NUMBER,
                            to_account_number=bank_account.account_number,
                            amount=float(total_dividend),
                            currency='JPY',
                            description=description
                        )
                        deposit_result = True
                    except Exception as e:
                        print(f"[配当金] 振込エラー (user_id={holding.user_id}): {e}")
                        deposit_result = False

                    if deposit_result:
                        # 配当金支払い記録を作成
                        dividend_payment = DividendPayment(
                            user_id=holding.user_id,
                            symbol_id=stock.symbol_id,
                            quantity=holding.quantity,
                            dividend_per_share=dividend_per_share,
                            total_dividend=total_dividend,
                            stock_account_id=holding.stock_account_id
                        )
                        db.add(dividend_payment)

                        total_paid += float(total_dividend)
                        success_count += 1
                    else:
                        print(f"[配当金] 銀行口座への入金失敗 (user_id={holding.user_id})")
                        fail_count += 1

                except Exception as e:
                    print(f"[配当金] 個別処理エラー (user_id={holding.user_id}): {e}")
                    fail_count += 1
                    continue

            db.commit()
            print(f"[配当金支払い] 完了 - 成功: {success_count}件, 失敗: {fail_count}件, 合計: ¥{total_paid:,.0f}")

        except Exception as e:
            import traceback
            db.rollback()
            print(f"[配当金支払い] システムエラー: {e}")
            print(f"エラー詳細:\n{traceback.format_exc()}")
        finally:
            db.close()
            bank_db.close()

    @staticmethod
    def get_price_history(symbol_code: str, limit: int = 100) -> List[Dict]:
        """株価履歴を取得"""
        db = SessionLocal()
        try:
            stock = db.query(StockSymbol).filter_by(symbol_code=symbol_code).first()
            if not stock:
                return []

            history = db.query(StockPriceHistory)\
                .filter_by(symbol_id=stock.symbol_id)\
                .order_by(StockPriceHistory.timestamp.desc())\
                .limit(limit).all()

            return [{
                'price': h.price,
                'volume': h.volume,
                'timestamp': h.timestamp
            } for h in reversed(history)]  # 古い順に返す
        finally:
            db.close()

    @staticmethod
    def get_recent_events(symbol_code: str = None, limit: int = 10) -> List[Dict]:
        """最近のイベントを取得"""
        db = SessionLocal()
        try:
            query = db.query(StockEvent)

            if symbol_code:
                stock = db.query(StockSymbol).filter_by(symbol_code=symbol_code).first()
                if stock:
                    query = query.filter_by(symbol_id=stock.symbol_id)

            events = query.order_by(StockEvent.occurred_at.desc()).limit(limit).all()

            result = []
            for e in events:
                stock = db.query(StockSymbol).filter_by(symbol_id=e.symbol_id).first()
                result.append({
                    'event_id': e.event_id,
                    'symbol_code': stock.symbol_code if stock else None,
                    'name': stock.name if stock else None,
                    'event_type': e.event_type,
                    'event_text': e.event_text,
                    'impact': float(e.impact),
                    'occurred_at': e.occurred_at
                })
            return result
        finally:
            db.close()


# サービスインスタンス
price_service = PriceService()
