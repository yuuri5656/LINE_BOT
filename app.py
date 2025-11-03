from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import random
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

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
    user_id = event.source.user_id  # ← ここでユーザーIDを取得
    print("User ID:", user_id)      # Renderのログで確認可能

    text = event.message.text
    # ↓例：?userid で自分のIDを返信
    if text == "?userid":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"あなたのユーザーIDは\n{user_id}\nです。")
        )
        return
    if text == "?塩爺の好きな食べ物は？":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="草ｗｗｗ")
        )
    if text == "?おみくじ":
        num = random.randint(1, 8)
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
        line_bot_api.reply_message(
            event.reply_token,
            messages=[
                TextSendMessage(text=mess1),
                TextSendMessage(text=mess2)
            ]
        )
    if text == "?ほんちゃんはゲイ？":
        num = random.randint(1,3)
        if num == 1 or num == 2:
            mess = "少し。。。"
        else:
            mess = "はいそうです！！！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mess)
        )
    if text.startswith("?RPN"):
        tokens = text.split()[1:]  # "?RPN"の後ろの部分
        stack = []

        try:
            for token in tokens:
                if token.isdigit():
                    stack.append(int(token))
                elif token in "+-*/":
                    if len(stack) < 2:
                        raise ValueError("演算子の前に十分なオペランドがありません")
                    b = stack.pop()
                    a = stack.pop()
                    if token == "+": stack.append(a + b)
                    elif token == "-": stack.append(a - b)
                    elif token == "*": stack.append(a * b)
                    elif token == "/":
                        if b == 0:
                            raise ZeroDivisionError("0で割ろうとしました")
                        stack.append(a // b)
                else:
                    raise ValueError(f"不正なトークン: {token}")

            if len(stack) != 1:
                raise ValueError("式の構文が正しくありません")

            result = str(stack[0])

        except Exception as e:
            result = f"エラー: {e}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    if text == "?おみくじを何回も引くのは犯罪ですか？":
        num = random.randint(1,3)

        if num == 1:
            mess = "結論:死刑！"
        elif num == 2:
            mess = "ｼｵｼﾞ様に限り合法"
        elif num == 3:
            mess = "開示だな。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mess)
        )
    if text == "?ほんちゃんは童貞？":
        num = random.randint(1,6)

        if num == 1:
            result = "同級生とノリで卒業しましたｗ"
        elif num == 2:
            result = "ソープランドで卒業しました。"
        elif num == 3:
            result = "ﾌｰｿﾞｸに行きましたが卒業できませんでした。"
        elif num == 4:
            result = "JSにレ……この続きは当局により規制されました。"
        elif num == 5:
            result = "実は。。。。まだチェリーボーイ？"
        else:
            result = "ｼｵｼﾞと。。。。？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    if user_id == "U2fca94c4700a475955d241b2a7ed1a15" or text == "?mesugaki":
        num = random.randint(1,12)
        if num == 1:
            result = "ん…くっさぁ…♡"
        elif num == 2:
            result = "ほんちゃん♡♡イケメンっ///♡"
        elif num == 3:
            result = "ほんちゃん♡♡すっごいイケボｯｯｯ♡"
        elif num == 4:
            result = "ざぁこ♡ざぁこ♡"
        elif num == 5:
            result = "ざぁこ♡オレの勝ち♡♡何で負けたか明日までに考えといて下さい♡♡♡"
        elif num == 6:
            result = "ほらほら♡がんばれ♡がんばれ♡"
        
        if num <= 6:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=result)
            )
    if user_id == "U97337d58d0553ff88495f42085dd94eb" or text == "?tyobun":
        word = [
            "私", "あなた", "彼", "彼女", "これ", "それ", "あれ", "ここ", "そこ", "あそこ",
            "誰", "何", "いつ", "どこ", "どう", "なぜ", "もし", "だから", "しかし", "そして",
            "人", "男", "女", "子供", "友達", "家族", "父", "母", "兄", "姉", "弟", "妹",
            "犬", "猫", "鳥", "魚", "馬", "牛", "羊", "豚", "猿", "象", "兎", "虎", "龍",
            "山", "川", "海", "森", "空", "雲", "雨", "風", "雪", "星", "月", "太陽",
            "学校", "会社", "店", "駅", "家", "道", "車", "電車", "飛行機", "船", "自転車",
            "机", "椅子", "本", "ノート", "鉛筆", "消しゴム", "時計", "電話", "パソコン",
            "服", "靴", "帽子", "鞄", "眼鏡", "手", "足", "頭", "顔", "体", "心",
            "食べる", "飲む", "見る", "聞く", "話す", "行く", "来る", "帰る", "立つ", "座る",
            "歩く", "走る", "寝る", "起きる", "笑う", "泣く", "怒る", "遊ぶ", "学ぶ", "教える",
            "書く", "読む", "使う", "作る", "買う", "売る", "待つ", "持つ", "会う", "思う",
            "美しい", "楽しい", "悲しい", "嬉しい", "寂しい", "大きい", "小さい", "新しい",
            "古い", "高い", "低い", "広い", "狭い", "強い", "弱い", "長い", "短い", "赤い",
            "青い", "白い", "黒い", "黄色い", "甘い", "辛い", "速い", "遅い",
            "すぐに", "とても", "少し", "たくさん", "もう", "まだ", "いつも", "たまに", "よく",
            "全然", "本当に", "必ず", "もちろん", "まず", "次に", "最後に", "例えば",
            "こんにちは", "こんばんは", "ありがとう", "ごめんなさい", "おはよう", "さようなら",
            "はい", "いいえ", "うん", "へえ", "わあ", "ああ", "おお", "ふむ", "なるほど",
            "ねえ", "なあ", "よし", "さて", "ところで", "つまり", "だから", "それで", "けれど",
            "朕", "余", "吾輩", "妾", "わし", "おぬし", "貴様", "拙者", "俺様", "小生",
            "バナナ", "カレー", "ピザ", "ラーメン", "寿司", "たこ焼き", "餃子", "うどん",
            "おにぎり", "焼肉", "チョコ", "ケーキ", "団子", "羊羹", "抹茶", "梅干し",
            "カエル", "カラス", "たぬき", "きつね", "ペンギン", "ナマケモノ", "カピバラ",
            "謎", "虚無", "混沌", "永遠", "時間", "空間", "次元", "運命", "真理", "夢",
            "闇", "光", "音", "沈黙", "波動", "量子", "心臓", "魂", "記憶", "幻",
            "わらわ", "朧", "霞", "影", "零", "漆黒", "紅蓮", "翠", "琥珀", "蒼穹",
            "きらめき", "ほのか", "もふもふ", "ふにゃ", "ぴえん", "うぇーい", "へっぽこ",
            "ばか", "天才", "凡人", "変人", "神", "悪魔", "妖精", "幽霊", "忍者", "侍",
            "博士", "王", "姫", "騎士", "魔法使い", "勇者", "村人", "商人", "詩人",
            "猫耳", "尻尾", "翼", "角", "魔力", "剣", "盾", "宝石", "鍵", "扉", "鏡",
            "未来", "過去", "現在", "永劫", "一瞬", "希望", "絶望", "約束", "真実", "嘘",
            "にゃん", "わん", "ぴょん", "がおー", "むにゃ", "ふわふわ", "どや", "むっ", "すん",
            "おこ", "ぷん", "にっこり", "うとうと", "ぐすん", "しょぼん", "てへ", "ほっこり"
        ]

        length = random.randint(30, 100)
        result = ""
        for _ in range(length):
            result += random.choice(word)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
