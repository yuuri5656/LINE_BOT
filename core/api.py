from linebot import LineBotApi, WebhookHandler
import config
import requests

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)


def show_loading_animation(chat_id: str, loading_seconds: int = 5):
    """
    個人チャットでローディングアニメーションを表示する

    Args:
        chat_id: ユーザーID（個人チャット）
        loading_seconds: ローディング表示秒数（5, 10, 20, 30, 40, 50, 60のいずれか。デフォルト5秒）

    Note:
        - グループチャットや複数人トークでは使用不可
        - 個人チャット (1:1) のみで有効
    """
    # 有効な秒数のみ許可
    valid_seconds = [5, 10, 20, 30, 40, 50, 60]
    if loading_seconds not in valid_seconds:
        loading_seconds = 5  # デフォルト値

    url = "https://api.line.me/v2/bot/chat/loading/start"
    headers = {
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "chatId": chat_id,
        "loadingSeconds": loading_seconds
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code != 202:
            print(f"[Loading Animation] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[Loading Animation] Exception: {e}")