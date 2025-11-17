import os

def _get_env_or_raise(key: str) -> str:
	val = os.environ.get(key)
	if not val:
		raise RuntimeError(f"Required environment variable '{key}' is not set")
	return val

LINE_CHANNEL_SECRET = _get_env_or_raise('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = _get_env_or_raise('LINE_CHANNEL_ACCESS_TOKEN')
DATABASE_URL = _get_env_or_raise('DATABASE_URL')
# 任意: 管理者/作成者のLINE userId。設定されていれば口座作成完了通知を個別送信する。
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID')
