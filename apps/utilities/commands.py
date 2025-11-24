"""
ユーティリティコマンドハンドラー（時間割、おみくじ等）
"""
from linebot.models import TextSendMessage
from core.api import line_bot_api
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
import psycopg2
import config


def check_message_today(conn, user_id, message):
    """今日既に同じメッセージを送信したかチェック"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM logs
            WHERE user_id = %s
            AND message LIKE %s
            AND (sent_at AT TIME ZONE 'Asia/Tokyo')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tokyo')::date
        """, (user_id, message))
        count = cur.fetchone()[0]
        return count > 1


def handle_userid(event, user_id):
    """ユーザーID表示コマンド"""
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"あなたのユーザーIDは\n{user_id}\nです。")
    )


def handle_help(event):
    """ヘルプ表示コマンド"""
    from apps.help_flex import get_help_flex
    line_bot_api.reply_message(event.reply_token, get_help_flex())


def handle_timetable(event):
    """明日の時間割表示コマンド"""
    messages = []
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
    if weekday_num < 5:
        messages.append(TextSendMessage(text=f"明日、{tomorrow.month}月{tomorrow.day}日{weekday_jp}曜日のC組の時間割は以下の通り。"))
        subject_message = ""
        for i in range(len(subject[weekday_num])):
            subject_message += f"{i+1}時間目: {subject[weekday_num][i]}\n"
        subject_message = subject_message.strip()
        messages.append(TextSendMessage(text=subject_message))
    else:
        messages.append(TextSendMessage(text=f"明日、{tomorrow.month}月{tomorrow.day}日{weekday_jp}曜日は学校がありません。"))
    messages.append(TextSendMessage(text="※この時間割はあくまで予定であり、実際の時間割とは異なる場合があります。"))
    line_bot_api.reply_message(event.reply_token, messages)


def handle_omikuji(event, user_id, display_name, text):
    """おみくじコマンド"""
    conn = psycopg2.connect(config.DATABASE_URL)
    messages = []
    if not check_message_today(conn, user_id, text) or user_id == "Ubada9dde68b83179125cba4bc0b5633c":
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
    else:
        messages.append(TextSendMessage(text="御神籤は一日に一度迄です。\n許されるのは塩路様だけです。"))
    
    line_bot_api.reply_message(event.reply_token, messages)
    if conn:
        conn.close()


def handle_rpn(event, text):
    """逆ポーランド記法計算コマンド"""
    tokens = text.split()[1:]
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
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))


def handle_setname(event, user_id, text):
    """名前設定コマンド"""
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
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="名前を保存しました。")
        )
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


def handle_fun_commands(event, text):
    """お遊びコマンド群"""
    if text == "?塩爺の好きな食べ物は？":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="草ｗｗｗ"))
        return True
    
    if text == "?ほんちゃんはゲイ？":
        num = random.randint(1, 3)
        mess = "少し。。。" if num in [1, 2] else "はいそうです！！！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=mess))
        return True
    
    if text == "?おみくじを何回も引くのは犯罪ですか？":
        num = random.randint(1, 3)
        mess = "結論:死刑！" if num == 1 else ("ｼｵｼﾞ様に限り合法" if num == 2 else "開示だな。")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=mess))
        return True
    
    if text == "?ほんちゃんは童貞？":
        num = random.randint(1, 6)
        results = [
            "同級生とノリで卒業しましたｗ",
            "ソープランドで卒業しました。",
            "ﾌｰｿﾞｸに行きましたが卒業できませんでした。",
            "JSにレ……この続きは当局により規制されました。",
            "実は。。。。まだチェリーボーイ？",
            "ｼｵｼﾞと。。。。？"
        ]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=results[num-1]))
        return True
    
    return False


def handle_default_user_message(event):
    """個別チャットのデフォルト応答"""
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="塩爺です。?ヘルプ と入力すると利用可能なコマンド一覧が表示されます。")
    )
