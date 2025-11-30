"""
株式トレードセッション管理

購入・売却フローの状態管理
"""
from typing import Dict, Any, Optional


class StockSessionManager:
    """株式トレード用セッション管理"""

    def __init__(self):
        self._sessions: Dict[str, Any] = {}

    def start_trade_session(self, user_id: str, trade_type: str, symbol_code: str):
        """
        取引セッション開始

        Args:
            user_id: ユーザーID
            trade_type: 'buy' or 'sell'
            symbol_code: 銘柄コード
        """
        self._sessions[user_id] = {
            'type': 'stock_trade',
            'trade_type': trade_type,
            'symbol_code': symbol_code,
            'step': 'quantity'
        }

    def start_account_registration_session(self, user_id: str, accounts: list):
        """
        株式口座登録セッション開始

        Args:
            user_id: ユーザーID
            accounts: 銀行口座リスト
        """
        self._sessions[user_id] = {
            'type': 'stock_account_registration',
            'step': 'select_account' if len(accounts) > 1 else 'confirm',
            'accounts': accounts,
            'selected_account_id': accounts[0]['account_id'] if len(accounts) == 1 else None
        }

    def update_session(self, user_id: str, data: Dict):
        """セッション更新"""
        if user_id in self._sessions:
            self._sessions[user_id].update(data)

    def get_session(self, user_id: str) -> Optional[Dict]:
        """セッション取得"""
        return self._sessions.get(user_id)

    def end_session(self, user_id: str):
        """セッション終了"""
        self._sessions.pop(user_id, None)

    def has_session(self, user_id: str) -> bool:
        """セッション存在確認"""
        return user_id in self._sessions

    def get_session_type(self, user_id: str) -> Optional[str]:
        """セッションタイプ取得"""
        session = self.get_session(user_id)
        return session.get('type') if session else None


# グローバルインスタンス
stock_session_manager = StockSessionManager()
