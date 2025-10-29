import requests

# ---- 設定 ----
CHANNEL_ACCESS_TOKEN = "ここにチャネルアクセストークン"
GROUP_ID = "ここにグループID"

# ---- メッセージ ----
message = "こんにちは！これはテストメッセージです。"

# ---- リクエスト送信 ----
url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
data = {
    "to": GROUP_ID,
    "messages": [
        {"type": "text", "text": message}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code, response.text)
