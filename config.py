import os

def _get_env_or_raise(key: str) -> str:
	val = os.environ.get(key)
	if not val:
		raise RuntimeError(f"Required environment variable '{key}' is not set")
	return val

LINE_CHANNEL_SECRET = _get_env_or_raise('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = _get_env_or_raise('LINE_CHANNEL_ACCESS_TOKEN')
DATABASE_URL = _get_env_or_raise('DATABASE_URL')
