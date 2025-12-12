from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from core.api import handler
import core.handler
from apps.stock.background_updater import start_background_updater
from apps.prison.rehabilitation_scheduler import start_rehabilitation_distribution_scheduler
from apps.rich_menu import create_rich_menus, set_default_rich_menu

app = Flask(__name__)

# 株価バックグラウンド更新を開始
start_background_updater()

# 懲役システムの給付金配布スケジューラーを開始
start_rehabilitation_distribution_scheduler()

# リッチメニューの初期化（起動時に自動作成）
try:
    print("[起動] リッチメニューを初期化中...")
    create_rich_menus()
    set_default_rich_menu()
    print("[起動] リッチメニューの初期化が完了しました")
except Exception as e:
    print(f"[起動] リッチメニューの初期化に失敗しました: {e}")
    print("[起動] 手動で ?メニュー作成 コマンドを実行して作成してください")

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
