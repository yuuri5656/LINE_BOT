from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import config
import random
import psycopg2

def auto_reply(event, text, user_id, group_id):
    conn = None
    cur = None
    
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
    elif text == "?おみくじ":
        messages = []

        # cur.execute("SELECT my_name FROM users WHERE line_id = %s", (user_id,))
        # result = cur.fetchone()
        # if result[0] != "not_set" or result[0] != "":
        #     messages.append(TextSendMessage(text=result[0]+"さんの運勢は……"))
        # else:
        #     messages.append(TextSendMessage(text="あなたの運勢は……"))

        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        messages.append(TextSendMessage(text=profile.display_name+"さんの運勢は……"))

        num = random.randint(1, 8)
        if num == 1:
            mess1 = ("大吉でした")
            mess2 = ("とても良い一日になるでしょう！……ﾊｱ羨ましい……")
        elif num == 2:
            mess1 = ("中吉でした")
            mess2 = ("そこそこ良い一日になるでしょう……マアマアやなあw")
        elif num == 3:
            mess1 = ("小吉でした")
            mess2 = ("いい感じですね！良い一日を！……微妙で草ｗ")
        elif num == 4:
            mess1 = ("吉でした")
            mess2 = ("いいですね！良い一日を！……ｷﾁｯ")
        elif num == 5:
            mess1 = ("末吉でした")
            mess2 = ("まあまあですね……ギリギリで草ｗ")
        elif num == 6:
            mess1 = ("凶でした")
            mess2 = ("まだいけますよ！良い一日を！……ﾌﾟｯｗ")
        elif num == 7:
            mess1 = ("小凶でした.....残念.........")
            mess2 = ("大丈夫です！良い一日を！……ﾄﾞﾝﾏｲｗ")
        else:
            mess1 = ("大凶でした")
            mess2 = ("気を取り直してください！良い一日を！……ﾀﾞｲｷｮｳﾀﾞｲｷｮｳｗｗｗ")

        messages.append(TextSendMessage(text=mess1))
        messages.append(TextSendMessage(text=mess2))

        line_bot_api.reply_message(
            event.reply_token, messages
        )
    elif text == "?ほんちゃんはゲイ？":
        num = random.randint(1,3)
        if num == 1 or num == 2:
            mess = "少し。。。"
        else:
            mess = "はいそうです！！！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mess)
        )
    elif text.startswith("?RPN"):
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

    elif text == "?おみくじを何回も引くのは犯罪ですか？":
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
    elif text == "?ほんちゃんは童貞？":
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
    elif user_id == "U2fca94c4700a475955d241b2a7ed1a15" or text == "?mesugaki":
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
    elif text.startswith("?setname"):
        if user_id not in ["U5631e4bcb598c6b7c59cde211bf32f27", "U2fca94c4700a475955d241b2a7ed1a15"]:
            my_name = "".join(text.split()[1:])
            if len(my_name) <= 1 or len(my_name) >= 20:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="名前が短すぎるか長すぎます。")
                )
            cur.execute("""
                INSERT INTO users (line_id, my_name)
                VALUES (%s, %s)
                ON CONFLICT (line_id)
                DO UPDATE SET my_name = EXCLUDED.my_name
            """, (user_id, my_name))
            conn.commit()
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="残念ながらあなたの名前は変えられませんｗｗｗ")
            )

    # データベースとの接続を切断
    if cur:
        cur.close()
    if conn:
        conn.close()