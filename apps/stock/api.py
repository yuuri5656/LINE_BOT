"""
株式トレードシステム 外部向けAPIファサード

外部からはこのファイルのみをインポートして使用すること
内部実装（stock_service.py等）への直接アクセスは禁止
"""
from typing import Optional, List, Dict, Tuple
from .stock_service import stock_service
from .price_service import price_service
from .chart_service import chart_service
from .session_manager import stock_session_manager


class StockAPI:
    """株式トレードシステムの統合API"""

    # === 口座管理 ===

    @staticmethod
    def create_stock_account(user_id: str, bank_account_id: int) -> Optional[Dict]:
        """株式口座を作成"""
        return stock_service.create_stock_account(user_id, bank_account_id)

    @staticmethod
    def get_stock_account(user_id: str) -> Optional[Dict]:
        """株式口座情報を取得"""
        return stock_service.get_stock_account(user_id)

    # === 銘柄情報 ===

    @staticmethod
    def get_all_stocks() -> List[Dict]:
        """全銘柄情報を取得"""
        return stock_service.get_all_stocks()

    @staticmethod
    def get_stock_by_code(symbol_code: str) -> Optional[Dict]:
        """銘柄コードから銘柄情報を取得"""
        return stock_service.get_stock_by_code(symbol_code)

    # === 保有株管理 ===

    @staticmethod
    def get_user_holdings(user_id: str) -> List[Dict]:
        """ユーザーの保有株一覧を取得"""
        return stock_service.get_user_holdings(user_id)

    # === 取引 ===

    @staticmethod
    def buy_stock(user_id: str, symbol_code: str, quantity: int) -> Tuple[bool, str, Optional[Dict]]:
        """株式を購入"""
        return stock_service.buy_stock(user_id, symbol_code, quantity)

    @staticmethod
    def sell_stock(user_id: str, symbol_code: str, quantity: int) -> Tuple[bool, str, Optional[Dict]]:
        """株式を売却"""
        return stock_service.sell_stock(user_id, symbol_code, quantity)

    @staticmethod
    def get_transaction_history(user_id: str, limit: int = 20) -> List[Dict]:
        """取引履歴を取得"""
        return stock_service.get_transaction_history(user_id, limit)

    # === 株価情報 ===

    @staticmethod
    def update_all_prices():
        """全銘柄の価格を更新（バックグラウンド用）"""
        price_service.update_all_prices()

    @staticmethod
    def execute_ai_trading():
        """AIトレーダーの取引を実行（バックグラウンド用）"""
        price_service.execute_ai_trading()

    @staticmethod
    def pay_dividends():
        """配当金を支払い（バックグラウンド用）"""
        price_service.pay_dividends()

    @staticmethod
    def get_price_history(symbol_code: str, limit: int = 100) -> List[Dict]:
        """株価履歴を取得"""
        return price_service.get_price_history(symbol_code, limit)

    @staticmethod
    def get_recent_events(symbol_code: str = None, limit: int = 10) -> List[Dict]:
        """最近のイベントを取得"""
        return price_service.get_recent_events(symbol_code, limit)

    # === チャート生成 ===

    @staticmethod
    def generate_stock_chart(symbol_code: str, days: int = 30) -> Optional[str]:
        """株価チャートを生成（Base64エンコード画像）"""
        return chart_service.generate_stock_chart(symbol_code, days)

    @staticmethod
    def generate_portfolio_chart(holdings: List[Dict]) -> Optional[str]:
        """ポートフォリオチャートを生成"""
        return chart_service.generate_portfolio_chart(holdings)

    @staticmethod
    def generate_comparison_chart(holdings: List[Dict]) -> Optional[str]:
        """保有株損益比較チャートを生成"""
        return chart_service.generate_comparison_chart(holdings)

    # === セッション管理 ===

    @staticmethod
    def start_trade_session(user_id: str, trade_type: str, symbol_code: str):
        """取引セッション開始"""
        stock_session_manager.start_trade_session(user_id, trade_type, symbol_code)

    @staticmethod
    def start_account_registration_session(user_id: str, accounts: list):
        """株式口座登録セッション開始"""
        stock_session_manager.start_account_registration_session(user_id, accounts)

    @staticmethod
    def update_session(user_id: str, data: Dict):
        """セッション更新"""
        stock_session_manager.update_session(user_id, data)

    @staticmethod
    def get_session(user_id: str) -> Optional[Dict]:
        """セッション取得"""
        return stock_session_manager.get_session(user_id)

    @staticmethod
    def end_session(user_id: str):
        """セッション終了"""
        stock_session_manager.end_session(user_id)

    @staticmethod
    def has_session(user_id: str) -> bool:
        """セッション存在確認"""
        return stock_session_manager.has_session(user_id)


# グローバルAPIインスタンス
stock_api = StockAPI()
