"""
ユーザーセッション管理モジュール
"""
from typing import Dict, Any

# ユーザーIDをキーとしたセッション情報を保持する辞書
sessions: Dict[str, Any] = {}