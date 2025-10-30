import requests

# ---- 設定 ----
CHANNEL_ACCESS_TOKEN = "s1mjVUw5pRMoGE5GeVaacpYiEJgj561EbudGSQlm17JahyLIlVpnZi/GchGsp0XSzJE33BLGOiYAHXTJL9Ryk5aLU28zt2mRCC7cOOGOljfLIJttB2AD6ut4Et1I1HWubhI5/XHBkwtcV+Hy7OOKmwdB04t89/1O/w1cDnyilFU="
GROUP_ID = "C76594d544af27b7c51f332f341b345b4"

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
