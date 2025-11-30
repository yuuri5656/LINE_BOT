from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from core.api import handler
import core.handler
from apps.stock.background_updater import start_background_updater

app = Flask(__name__)

# 株価バックグラウンド更新を開始
start_background_updater()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
