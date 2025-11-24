"""
銀行機能専用セッション管理
"""
from typing import Dict, Any, Optional


class BankingSessionManager:
    """銀行機能のセッション管理クラス"""
    
    def __init__(self):
        self._sessions: Dict[str, Any] = {}
    
    def get(self, user_id: str) -> Optional[Any]:
        """セッション取得"""
        return self._sessions.get(user_id)
    
    def set(self, user_id: str, data: Any):
        """セッション設定"""
        self._sessions[user_id] = data
    
    def delete(self, user_id: str):
        """セッション削除"""
        self._sessions.pop(user_id, None)
    
    def has_session(self, user_id: str) -> bool:
        """セッションの存在確認"""
        return user_id in self._sessions
    
    def clear(self):
        """全セッションをクリア"""
        self._sessions.clear()


# グローバルインスタンス
banking_session_manager = BankingSessionManager()
