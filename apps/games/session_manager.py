"""
ゲーム機能専用セッション管理
ゲームセッションはminigames.pyのGroupManagerで管理されているため、
このモジュールは補助的な役割を果たす
"""
from typing import Dict, Any, Optional
from apps.games.minigames import manager, GroupManager


class GameSessionManager:
    """ゲーム機能のセッション補助管理クラス"""
    
    def __init__(self):
        # グループゲームセッションはminigames.pyのmanagerで管理
        # ここでは個別チャット用の一時データなどを管理
        self._user_sessions: Dict[str, Any] = {}
    
    def get_user_session(self, user_id: str) -> Optional[Any]:
        """ユーザーセッション取得"""
        return self._user_sessions.get(user_id)
    
    def set_user_session(self, user_id: str, data: Any):
        """ユーザーセッション設定"""
        self._user_sessions[user_id] = data
    
    def delete_user_session(self, user_id: str):
        """ユーザーセッション削除"""
        self._user_sessions.pop(user_id, None)
    
    @staticmethod
    def get_group_manager() -> GroupManager:
        """グループゲームマネージャーを取得"""
        return manager
    
    @staticmethod
    def get_group_session(group_id: str):
        """グループゲームセッション取得"""
        return manager.get_session(group_id)
    
    def clear_user_sessions(self):
        """全ユーザーセッションをクリア"""
        self._user_sessions.clear()


# グローバルインスタンス
game_session_manager = GameSessionManager()
