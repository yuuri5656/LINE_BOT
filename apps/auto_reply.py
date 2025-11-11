from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import config
import random
import psycopg2
from apps.minigame.bank_reception import bank_reception
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def auto_reply(event, text, user_id, group_id, display_name, sessions):
    conn = None
    cur = None
    state = sessions.get(user_id)

    # ユーザーチャットでの"?口座開設"メッセージを処理
    if text == "?口座開設" or (isinstance(state, dict) and state.get("step")):
        if event.source.type == 'user':  # ユーザーチャットのみ対応
            bank_reception(event, text, user_id, display_name, sessions)
            return

    if text == "?userid":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"あなたのユーザーIDは\n{user_id}\nです。")
        )
        return
    elif text == "?明日の時間割":
        messages = []
        subject_message = ""
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        today = now.date()
        tomorrow = today + timedelta(days=1)
        weekday_num = tomorrow.weekday()
        weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][weekday_num]
        subject = [
            ["学活", "音楽", "英語", "社会", "美術", "総合"],
            ["英語", "理科", "国語", "社会", "数学", "保体"],
            ["数学", "理科", "技術•家庭", "国語", "道徳"],
            ["保体", "英語", "理科", "国語", "数学", "社会"],
            ["英語", "数学", "社会", "保体", "理科", "総合"]
        ]
        if not weekday_num >= 5:
            messages.append(TextSendMessage(text=f"明日、{tomorrow.month}月{tomorrow.day}日{weekday_jp}曜日のC組の時間割は以下の通り。"))
            for i in range(len(subject[weekday_num])):
            subject_message += f"{i+1}時間目: {subject[weekday_num][i]}\n"
        subject_message = subject_message.strip()
        messages.append(TextSendMessage(text=subject_message))
        else:
            messages.append(TextSendMessage(text=f"明日、{tomorrow.month}月{tomorrow.day}日{weekday_jp}曜日は学校がありません。"))
        messages.append(TextSendMessage(text="※この時間割はあくまで予定であり、実際の時間割とは異なる場合があります。"))
        line_bot_api.reply_message(event.reply_token, messages)
        return
    elif text == "?塩爺の好きな食べ物は？":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="草ｗｗｗ")
        )
        return
    elif text == "?おみくじ":
        messages = []

        # cur.execute("SELECT my_name FROM users WHERE line_id = %s", (user_id,))
        # result = cur.fetchone()
        # if result[0] != "not_set" or result[0] != "":
        #     messages.append(TextSendMessage(text=result[0]+"さんの運勢は……"))
        # else:
        #     messages.append(TextSendMessage(text="あなたの運勢は……"))

        # handler already fetched profile.display_name; use it to avoid extra API calls
        messages.append(TextSendMessage(text=display_name+"さんの運勢は……"))

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
    # elif user_id == "U2fca94c4700a475955d241b2a7ed1a15" or text == "?mesugaki":
    #     num = random.randint(1,12)
    #     if num == 1:
    #         result = "ん…くっさぁ…♡"
    #     elif num == 2:
    #         result = "ほんちゃん♡♡イケメンっ///♡"
    #     elif num == 3:
    #         result = "ほんちゃん♡♡すっごいイケボｯｯｯ♡"
    #     elif num == 4:
    #         result = "ざぁこ♡ざぁこ♡"
    #     elif num == 5:
    #         result = "ざぁこ♡オレの勝ち♡♡何で負けたか明日までに考えといて下さい♡♡♡"
    #     elif num == 6:
    #         result = "ほらほら♡がんばれ♡がんばれ♡"

    #     if num <= 6:
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             TextSendMessage(text=result)
    #         )
    elif text.startswith("?setname"):
        # only allow certain users to be blocked from changing name
        if user_id in ["U5631e4bcb598c6b7c59cde211bf32f27", "U2fca94c4700a475955d241b2a7ed1a15"]:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="残念ながらあなたの名前は変えられませんｗｗｗ")
            )
            return

        my_name = "".join(text.split()[1:])
        if len(my_name) <= 1 or len(my_name) >= 20:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="名前が短すぎるか長すぎます。")
            )
            return

        # open DB connection only when we need to write
        try:
            conn = psycopg2.connect(config.DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (line_id, my_name)
                VALUES (%s, %s)
                ON CONFLICT (line_id)
                DO UPDATE SET my_name = EXCLUDED.my_name
            """, (user_id, my_name))
            conn.commit()
        except Exception as e:
            print("DB Error (setname):", e)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="名前の保存中にエラーが発生しました。")
            )
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    elif text == "?じゃんけん":
        messages = []
        sessions[user_id] = "waiting_for_hand"
        messages.append(TextSendMessage(text="最初はグー！じゃんけん……"))
        line_bot_api.reply_message(
            event.reply_token,
            messages
        )
        return

    elif state == "waiting_for_hand":
        messages = []
        if text in ["グー", "ぐー", "チョキ", "ちょき", "パー", "ぱー"]:
            # 入力を標準形に変換
            hand = {"ぐー": "グー", "ちょき": "チョキ", "ぱー": "パー"}.get(text, text)
            # 必ず勝つ手を選ぶ
            win_hand = {"グー": "パー", "チョキ": "グー", "パー": "チョキ"}[hand]
            messages.append(TextSendMessage(text=f"ﾎﾟﾝｯｯ!{win_hand}\n俺の勝ち!俺の勝ち!"))
            messages.append(TextSendMessage(text="何で負けたか明日までに考えといてください。\nそしたら何かが見えてくるはずです。"))
            messages.append(TextSendMessage(text="ほな、いただきます。"))
            messages.append(ImageSendMessage(
                original_content_url='https://i.imgur.com/HV1x5vV.png',
                preview_image_url='https://i.imgur.com/HV1x5vV.png'
            ))
        else:
            messages.append(TextSendMessage(text="逃げるな卑怯者！！！じゃんけんから逃げるなーーー！！！"))

        # セッション状態をクリア
        sessions.pop(user_id, None)

        # 応答を送信
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # データベースとの接続を切断
    if cur:
        cur.close()
    if conn:
        conn.close()
