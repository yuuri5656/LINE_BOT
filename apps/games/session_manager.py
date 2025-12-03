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


class IndividualGameSessionManager:
    """個別チャット用ゲームセッション管理クラス"""

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def create_session(self, user_id: str, game_type: str, session_data: Dict = None) -> Dict:
        """
        セッション作成

        Args:
            user_id: ユーザーID
            game_type: ゲームタイプ（'blackjack', 'roulette', etc.）
            session_data: 初期セッションデータ

        Returns:
            Dict: 作成されたセッション
        """
        session = {
            'type': 'betting',  # 'betting', 'playing', 'finished'
            'game_type': game_type,
            'current_bet': 0,
            'locked_chips': 0,
            'created_at': None
        }

        if session_data:
            session.update(session_data)

        self._sessions[user_id] = session
        return session

    def get_session(self, user_id: str) -> Optional[Dict]:
        """
        セッション取得

        Args:
            user_id: ユーザーID

        Returns:
            Optional[Dict]: セッションデータ
        """
        return self._sessions.get(user_id)

    def update_session(self, user_id: str, updates: Dict) -> bool:
        """
        セッション更新

        Args:
            user_id: ユーザーID
            updates: 更新データ

        Returns:
            bool: 更新成功か
        """
        if user_id in self._sessions:
            self._sessions[user_id].update(updates)
            return True
        return False

    def clear_session(self, user_id: str):
        """
        セッション削除

        Args:
            user_id: ユーザーID
        """
        self._sessions.pop(user_id, None)

    def has_session(self, user_id: str) -> bool:
        """
        セッション存在チェック

        Args:
            user_id: ユーザーID

        Returns:
            bool: セッションが存在するか
        """
        return user_id in self._sessions

    def is_playing(self, user_id: str) -> bool:
        """
        プレイ中かチェック

        Args:
            user_id: ユーザーID

        Returns:
            bool: プレイ中か
        """
        session = self.get_session(user_id)
        return session and session.get('type') == 'playing'

    def get_all_sessions(self) -> Dict[str, Dict]:
        """
        全セッション取得

        Returns:
            Dict[str, Dict]: 全セッションデータ
        """
        return self._sessions.copy()


# グローバルインスタンス
game_session_manager = GameSessionManager()
individual_game_manager = IndividualGameSessionManager()
