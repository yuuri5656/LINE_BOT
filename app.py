from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import random

app = Flask(__name__)

line_bot_api = LineBotApi('s1mjVUw5pRMoGE5GeVaacpYiEJgj561EbudGSQlm17JahyLIlVpnZi/GchGsp0XSzJE33BLGOiYAHXTJL9Ryk5aLU28zt2mRCC7cOOGOljfLIJttB2AD6ut4Et1I1HWubhI5/XHBkwtcV+Hy7OOKmwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('654a672e3e8e2131c5ed60de09b94707')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text == "?塩爺の好きな食べ物は？":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="草ｗｗｗ")
        )
    if text == "?おみくじ":
        line_bot_api.reply_message(
            event.reply_token,
            num = random.randint(1,8)
            if num == 1:
                mess1 = ("大吉でした")
                mess2 = ("とても良い一日になるでしょう！")
            elif num == 2:
                mess1 = ("中吉でした")
                mess2 = ("そこそこ良い一日になるでしょう")
            elif num == 3:
                mess1 = ("小吉でした")
                mess2 = ("いい感じですね！良い一日を！")
            elif num == 4:
                mess1 = ("吉でした")
                mess2 = ("いいですね！良い一日を！")
            elif num == 5:
                mess1 = ("末吉でした")
                mess2 = ("まあまあですね")
            elif num == 6:
                mess1 = ("凶でした")
                mess2 = ("まだいけますよ！良い一日を！")
            elif num == 7:
                mess1 = ("小凶でした.....残念.........")
                mess2 = ("大丈夫です！良い一日を！")
            else:
                mess1 = ("大凶でした")
                mess2 = ("気を取り直してください！良い一日を！")
            TextSendMessage(text=mess1)
            TextSendMessage(text=mess2)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
