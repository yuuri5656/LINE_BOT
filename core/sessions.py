"""
ユーザーセッション管理モジュール（統合インターフェース）
各機能専用のセッションマネージャーへのアクセスを提供
"""
from typing import Dict, Any, Optional


class UnifiedSessionManager:
    """統合セッションマネージャー
    
    各機能のセッションマネージャーを遅延ロードで取得し、
    統一されたインターフェースを提供する
    """
    
    def __init__(self):
        self._banking_manager = None
        self._game_manager = None
        # 後方互換性のための辞書インターフェース
        self._legacy_sessions: Dict[str, Any] = {}
    
    @property
    def banking(self):
        """銀行セッションマネージャーを取得"""
        if self._banking_manager is None:
            from apps.banking.session_manager import banking_session_manager
            self._banking_manager = banking_session_manager
        return self._banking_manager
    
    @property
    def game(self):
        """ゲームセッションマネージャーを取得"""
        if self._game_manager is None:
            from apps.games.session_manager import game_session_manager
            self._game_manager = game_session_manager
        return self._game_manager
    
    # 後方互換性のための辞書風メソッド
    def get(self, user_id: str) -> Optional[Any]:
        """セッション取得（銀行セッションを優先）"""
        # まず銀行セッションを確認
        banking_session = self.banking.get(user_id)
        if banking_session is not None:
            return banking_session
        
        # レガシーセッションを確認
        return self._legacy_sessions.get(user_id)
    
    def __getitem__(self, user_id: str) -> Any:
        """辞書風アクセス"""
        result = self.get(user_id)
        if result is None:
            raise KeyError(user_id)
        return result
    
    def __setitem__(self, user_id: str, value: Any):
        """辞書風設定（銀行セッションに保存）"""
        self.banking.set(user_id, value)
    
    def __delitem__(self, user_id: str):
        """辞書風削除"""
        self.banking.delete(user_id)
        self._legacy_sessions.pop(user_id, None)
    
    def pop(self, user_id: str, default=None):
        """辞書風pop"""
        self.banking.delete(user_id)
        return self._legacy_sessions.pop(user_id, default)
    
    def __contains__(self, user_id: str) -> bool:
        """辞書風in演算子"""
        return self.banking.has_session(user_id) or user_id in self._legacy_sessions


# グローバルインスタンス（後方互換性のため）
_unified_manager = UnifiedSessionManager()
sessions = _unified_manager  # 既存コードとの互換性を保つ
