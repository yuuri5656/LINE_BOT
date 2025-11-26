"""
ショップ機能専用セッション管理
"""
from typing import Dict, Any, Optional


class ShopSessionManager:
    """ショップ機能のセッション管理クラス"""

    def __init__(self):
        self._sessions: Dict[str, Any] = {}

    def get_session(self, user_id: str) -> Optional[Any]:
        """セッション取得"""
        return self._sessions.get(user_id)

    def start_session(self, user_id: str, data: Any):
        """セッション開始"""
        self._sessions[user_id] = data

    def update_session(self, user_id: str, data: Any):
        """セッション更新"""
        self._sessions[user_id] = data

    def end_session(self, user_id: str):
        """セッション終了"""
        self._sessions.pop(user_id, None)

    def has_session(self, user_id: str) -> bool:
        """セッションの存在確認"""
        return user_id in self._sessions

    def clear(self):
        """全セッションをクリア"""
        self._sessions.clear()


# グローバルインスタンス
shop_session_manager = ShopSessionManager()
