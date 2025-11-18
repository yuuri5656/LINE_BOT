from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import config
import random
import psycopg2
from apps.minigame.minigames import Player, GameSession, Group, GroupManager, manager, join_game_session, reset_game_session, cancel_game_session, GameState
from apps.minigame.bank_reception import bank_reception
from apps.minigame.rps_game import play_rps_game
from apps.minigame import bank_service
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def check_message_today(conn, user_id, message):
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

def auto_reply(event, text, user_id, group_id, display_name, sessions):
    conn = None
    cur = None
    state = sessions.get(user_id)

    # ユーザーチャットでの"?口座開設"メッセージを処理
    if text == "?口座開設" or (isinstance(state, dict) and state.get("step")):
        if event.source.type == 'user':  # ユーザーチャットのみ対応
            bank_reception(event, text, user_id, display_name, sessions)
            return
    
    # ミニゲーム口座登録処理（個別チャットのみ）
    if text == "?ミニゲーム口座登録" or (isinstance(state, dict) and state.get("minigame_registration")):
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム口座登録は個別チャット(1対1トーク)でのみ利用可能です。"))
            return
        
        # セッション管理: ミニゲーム口座登録フロー
        if text == "?ミニゲーム口座登録":
            # 現在の口座情報を取得
            account_info = bank_service.get_account_info_by_user(user_id)
            minigame_info = bank_service.get_minigame_account_info(user_id)
            
            messages = []
            messages.append("【ミニゲーム口座登録】\n\n")
            messages.append("お持ちの口座から一つを選び、ミニゲーム専用口座として登録します。\n")
            messages.append("※新しい口座を作成するわけではありません。\n\n")
            
            if minigame_info:
                messages.append(f"現在登録中のミニゲーム口座:\n支店番号: {minigame_info.get('branch_code')}\n口座番号: {minigame_info.get('account_number')}\n残高: {minigame_info.get('balance')} {minigame_info.get('currency')}\n\n")
                messages.append("別の口座を登録する場合は、本人確認のため以下の情報を順番に入力してください。\n\n")
            else:
                messages.append("ミニゲーム口座が未登録です。\n")
                messages.append("本人確認のため、以下の情報を順番に入力してください。\n\n")
            
            messages.append("まず、登録したい口座の支店番号（3桁）を入力してください。\n")
            messages.append("例: 001\n\n")
            messages.append("※'?口座情報'コマンドで確認できます。\n")
            messages.append("※キャンセルする場合は「キャンセル」と入力してください。")
            
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="".join(messages)))
            
            # セッションに状態を保存（ステップ1: 支店番号入力）
            sessions[user_id] = {"minigame_registration": True, "step": 1}
            return
        
        elif isinstance(state, dict) and state.get("minigame_registration"):
            # キャンセル処理
            if text.strip().lower() in ["キャンセル", "cancel"]:
                sessions.pop(user_id, None)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム口座登録をキャンセルしました。"))
                return
            
            current_step = state.get("step", 1)
            
            # ステップ1: 支店番号入力
            if current_step == 1:
                branch_code = text.strip()
                
                if not branch_code.isdigit() or len(branch_code) != 3:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="支店番号は3桁の数字で入力してください。\n例: 001")
                    )
                    return
                
                sessions[user_id]["branch_code"] = branch_code
                sessions[user_id]["step"] = 2
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"支店番号: {branch_code}\n\n次に、登録したい口座の口座番号（7桁）を入力してください。\n\n※'?口座情報'コマンドで確認できます。")
                )
                return
            
            # ステップ2: 口座番号入力
            elif current_step == 2:
                account_number = text.strip()
                
                if not account_number.isdigit() or len(account_number) != 7:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="口座番号は7桁の数字で入力してください。")
                    )
                    return
                
                sessions[user_id]["account_number"] = account_number
                sessions[user_id]["step"] = 3
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"口座番号: {account_number}\n\n次に、口座開設時に登録したフルネーム（半角カタカナ）を入力してください。\n例: ﾎﾝﾀﾞ ﾊﾙｷ")
                )
                return
            
            # ステップ3: 氏名入力
            elif current_step == 3:
                full_name = text.strip()
                
                # カタカナチェック（簡易）
                import re
                is_hankaku = re.match(r'^[ｦ-ﾟ ]+$', full_name)
                
                if not is_hankaku or len(full_name.split(" ")) < 2:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="フルネームは半角カタカナで、苗字と名前の間にスペースを入れて入力してください。\n例: ﾎﾝﾀﾞ ﾊﾙｷ")
                    )
                    return
                
                sessions[user_id]["full_name"] = full_name
                sessions[user_id]["step"] = 4
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"氏名: {full_name}\n\n最後に、口座開設時に設定した4桁の暗証番号を入力してください。")
                )
                return
            
            # ステップ4: 暗証番号入力と登録処理
            elif current_step == 4:
                pin_code = text.strip()
                
                if not pin_code.isdigit() or len(pin_code) != 4:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="暗証番号は4桁の数字で入力してください。")
                    )
                    return
                
                # 登録処理を実行（生年月日なしバージョン）
                full_name = sessions[user_id].get("full_name")
                branch_code = sessions[user_id].get("branch_code")
                account_number = sessions[user_id].get("account_number")
                
                # 生年月日を取得するため、まず顧客情報を確認
                # authenticate_customerを使用するために、既存の顧客から生年月日を取得
                from apps.minigame.main_bank_system import SessionLocal, Customer
                from sqlalchemy import select
                
                db = SessionLocal()
                try:
                    customer = db.execute(select(Customer).filter_by(user_id=user_id)).scalars().first()
                    if customer:
                        date_of_birth = customer.date_of_birth.strftime("%Y-%m-%d")
                    else:
                        # 顧客が見つからない場合
                        sessions.pop(user_id, None)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="❌ 口座情報が見つかりません。先に '?口座開設' で口座を作成してください。")
                        )
                        return
                finally:
                    db.close()
                
                result = bank_service.register_minigame_account(
                    user_id=user_id,
                    full_name=full_name,
                    branch_code=branch_code,
                    account_number=account_number,
                    pin_code=pin_code,
                    date_of_birth=date_of_birth
                )
                
                # セッションをクリア
                sessions.pop(user_id, None)
                
                if result.get('success'):
                    update_text = "更新" if result.get('updated') else "登録"
                    message = f"✅ ミニゲーム用口座を{update_text}しました！\n\n支店番号: {branch_code}\n口座番号: {account_number}\n\nこの口座でミニゲームに参加できます。\n※この口座は通常の入出金も引き続き利用できます。"
                else:
                    error_msg = result.get('error', '不明なエラーが発生しました。')
                    message = f"❌ 登録に失敗しました。\n\n{error_msg}\n\n入力した情報が正しいか確認してください。\n・口座開設時に登録した氏名と暗証番号\n・登録したい口座の支店番号と口座番号\n\n'?口座情報'で口座番号を確認できます。"
                
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
                return

    if text == "?userid":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"あなたのユーザーIDは\n{user_id}\nです。")
        )
        return
    elif text == "?口座情報":
        # 個別チャットでのみ口座情報を表示
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="個別チャットでのみ利用可能です。塩爺に直接メッセージを送ってください。"))
            return

        info = bank_service.get_account_info_by_user(user_id)
        if not info:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="有効な口座が見つかりません。'?口座開設' を入力して口座を作成してください。"))
            return

        lines = []
        lines.append("口座情報:")
        lines.append(f"口座番号: {info.get('account_number')}")
        lines.append(f"残高: {info.get('balance') or '0.00'} {info.get('currency') or ''}")
        lines.append(f"種類: {info.get('type') or '（不明）'}")
        bc = info.get('branch_code') or ''
        bn = info.get('branch_name') or ''
        if bc or bn:
            lines.append(f"支店: {bc} {bn}")
        lines.append(f"状態: {info.get('status')}")
        if info.get('created_at'):
            try:
                lines.append(f"作成日: {info.get('created_at')}")
            except Exception:
                pass
        
        # ミニゲーム口座登録状況も表示
        minigame_info = bank_service.get_minigame_account_info(user_id)
        lines.append("\n【ミニゲーム口座】")
        if minigame_info:
            lines.append(f"登録済み: {minigame_info.get('account_number')}")
        else:
            lines.append("未登録 ('?ミニゲーム口座登録' で登録)")

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
        return
    elif text == "?通帳":
        # 個別チャットでのみ通帳（最近の履歴）を表示
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="個別チャットでのみ利用可能です。塩爺に直接メッセージを送ってください。"))
            return

        txs = bank_service.get_account_transactions_by_user(user_id, limit=20)
        if not txs:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="取引履歴が見つかりません。"))
            return

        # 履歴を整形して送信（長すぎる場合は要分割だが簡易実装）
        lines = ["最近の通帳（最新20件まで）:"]
        for t in txs:
            dt = t.get('executed_at')
            try:
                dt_str = dt.strftime("%Y-%m-%d %H:%M") if dt else "-"
            except Exception:
                dt_str = str(dt)
            other = t.get('other_account_number') or '―'
            lines.append(f"{dt_str} {t.get('direction')} {t.get('amount')}{t.get('currency') or ''} ({t.get('type')}) 相手: {other} 状態:{t.get('status')}")

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
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
        if weekday_num < 5:
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
        return
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
        return
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
            # 確認メッセージを送信してユーザーに保存成功を通知
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="名前を保存しました。")
            )
            return
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

    # じゃんけんゲーム関連のメッセージ処理
    if event.source.type == 'group':
        # そのグループに待機中もしくは開始中のゲームが無い場合、セッションを作成して募集を開始
        if text == "?じゃんけん" and event.source.type == 'group':
            grp = manager.groups.get(group_id, None)
            # そのグループでセッションが無ければ作成（play_rps_game がセッションを作る）
            if grp is None or grp.current_game is None:
                play_rps_game(event, user_id, text, display_name, group_id, sessions)
                return

            # セッションが存在する場合は状態に応じて案内
            state = getattr(grp.current_game, "state", None)
            if state == GameState.RECRUITING:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"{display_name} 様、現在このグループではゲームを募集中です。\n是非'?参加'と入力して参加してみてください。")
                )
                return
            if state == GameState.IN_PROGRESS:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"{display_name} 様、現在このグループではゲームが進行中です。\nしばらくお待ちの上、再度お試しください。")
                )
                return

        # 参加希望者は"?参加"と入力して参加表明を行う
        if text == "?参加" and event.source.type == 'group':
            conn = psycopg2.connect(config.DATABASE_URL)
            try:
                join_message = join_game_session(group_id, user_id, display_name, conn)
            finally:
                conn.close()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=join_message)
            )
            return

        # ホストまたは参加者が"?キャンセル"と入力して参加を取り消し可能とする
        if text == "?キャンセル":
            group = manager.groups.get(group_id)
            if not group or not group.current_game:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="セッションをキャンセル出来ませんでした。"))
                return

            # ホストはゲーム開始前なら中止可能（IN_PROGRESS でなければ中止可）
            # ホストはゲーム開始前であれば中止可能
            host_can_cancel = getattr(group.current_game, "state", None) != GameState.IN_PROGRESS

            if group.current_game.host_user_id == user_id and host_can_cancel:
                reset_game_session(group_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="ホストがキャンセルしたため、全員の参加を取り消しました。")
                )
                return

            # 参加者が自分の参加を取り消す（募集中のみ）
            participant_can_cancel = getattr(group.current_game, "state", None) == GameState.RECRUITING
            if participant_can_cancel:
                if user_id in group.current_game.players:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=cancel_game_session(group_id, user_id))
                    )
                    return

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="セッションをキャンセル出来ませんでした。")
            )
            return
        if text == "?開始":
            group = manager.groups.get(group_id)
            if group and group.current_game and group.current_game.state == GameState.RECRUITING and group.current_game.host_user_id == user_id:
                # ゲーム開始処理（参加者へ個別チャットで手を送るよう促す）
                # デフォルトタイムアウトは30秒（変更可）
                print(f"Players listed for game start: {group.current_game.players}")
                try:
                    from apps.minigame.minigames import start_game_session
                    msg = start_game_session(group_id, line_bot_api, timeout_seconds=30)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                except Exception as e:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ゲームの開始に失敗しました。"))
                return
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="ゲームを開始できませんでした。ホストのみが開始できます。")
                )
            return
    elif event.source.type == 'user':
        # ユーザーチャットでは、進行中のじゃんけんがある場合に手（グー/チョキ/パー）を受け付ける
        from apps.minigame.minigames import submit_player_move

        # 簡易的に手の候補を判定
        if text.strip() in ["グー","ぐー","チョキ","ちょき","パー","ぱー"]:
            res = submit_player_move(user_id, text.strip(), line_bot_api, reply_token=event.reply_token)
            # submit_player_move が自動で返信するためここでは戻り値のみ確認
            return

        # それ以外は通常の個別チャット用メッセージ（口座開設など）が処理されるため、簡易応答
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="塩爺です。?ヘルプ と入力すると利用可能なコマンド一覧が表示されます。")
        )
        return

    # データベースとの接続を切断
    if cur:
        cur.close()
    if conn:
        conn.close()
