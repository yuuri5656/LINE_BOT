from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import datetime
from apps.minigame.account_creation import create_account

def bank_reception(event, text, user_id, display_name, sessions):
    state = sessions.get(user_id)

    # セッションがあるかつ、それが辞書の場合は、その辞書のステップを取得
    if isinstance(state, dict):
        current_step = state.get("step")
    else:
        current_step = None

    # ステップ別のメッセージテンプレート
    step_messages = {
        1: TextSendMessage(text="ご自身のフルネームを教えてください。\n苗字と名前の間には半角スペースを挿入してください。(例:本田 春輝)"),
        2: TextSendMessage(text="ご自身の生年月日を「YYYY-MM-DD」の形式で教えてください。(例:2011-03-25)"),
        3: TextSendMessage(text="ご自身の希望する口座種別を、普通預金・当座預金・定期預金からお選び下さい。"),
        4: TextSendMessage(text="最後に、4桁の暗証番号を設定してください。(例:1234)\nまた、セキュリティの観点から、ご自身の誕生日や連続した数字、同じ数字の繰り返しは避けてください。")
    }

    # "?戻る"の処理
    if text == "?戻る" and isinstance(state, dict) and state.get("step"):
        current_step_num = state.get("step")
        if current_step_num > 1:
            # 前のステップに戻る
            prev_step = current_step_num - 1
            state["step"] = prev_step
            line_bot_api.reply_message(
                event.reply_token,
                step_messages[prev_step]
            )
            return

    # 口座開設
    if text == "?口座開設" and sessions.get(user_id) is None and event.source.type == 'user':
        messages = []
        sessions[user_id] = {"step": 1}
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=f"{display_name} 様、口座開設のご依頼を承りました。\nただいまから手続きを進めてまいりますので、以下の質問にお答えください。\nまた、手続き中は'?戻る'と入力することで、前の質問に戻ることができます。"),
            TextSendMessage(text="まず、ご自身のフルネームを教えてください。\nまた、苗字と名前の間には半角スペースを挿入してください。(例:本田 春輝)")]
        )
        return
    # 口座開設中のやり取り
    elif current_step == 1:
        full_name = text.strip()
        # 簡易的なバリデーション: スペースで区切られた2つ以上の単語があるか
        if len(full_name.split(" ")) >= 2:
            messages = []
            # セッションに顧客情報を保存する辞書を初期化（既に存在する場合は追加）
            if not isinstance(sessions.get(user_id), dict):
                sessions[user_id] = {"step": 2, "full_name": full_name}
            else:
                sessions[user_id]["full_name"] = full_name
                sessions[user_id]["step"] = 2

            messages.append(TextSendMessage(text=f"{display_name} 様、ありがとうございます。\n「{full_name} 様」で登録させて頂きます。"))
            messages.append(TextSendMessage(text="次に、ご自身の生年月日を「YYYY-MM-DD」の形式で教えてください。(例:2011-03-25)"))
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ございません。フルネームの形式が正しくありません。\n苗字と名前の間に半角スペースを挿入して、もう一度ご入力ください。(例:本田 春輝)")
            )
        return
    elif current_step == 2:
        birth_date_str = text.strip()
        try:
            birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            messages = []
            # セッションに生年月日を保存
            sessions[user_id]["birth_date"] = birth_date_str
            sessions[user_id]["step"] = 3

            messages.append(TextSendMessage(text=f"{display_name} 様、生年月日のご提供ありがとうございます。「{birth_date_str}」で登録させて頂きます。"))
            messages.append(TextSendMessage(text="次に、ご自身の希望する支店を以下から支店名でお選び下さい。\n※どの支店を選んで頂いてもご利用に影響はございません。"))
            messages.append(TextSendMessage(text="支店名　　　　支店番号\n塩路支店　　　001\nメガネ支店　　002\nバナナ支店　　003\nボラ部支店　　004\nゴリラ支店　　005\nマッコリ支店　006\nビースト支店　810"))
            # messages.append(TextSendMessage(text="次に、ご自身の希望する口座種別を、普通預金・定期預金からお選び下さい。"))
            line_bot_api.reply_message(
                event.reply_token,
                messages
            )
        except ValueError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ございません。生年月日の形式が正しくありません。\n「YYYY-MM-DD」の形式で再度ご入力ください。(例:2011-03-25)")
            )
        return
    elif current_step == 3:
        messages= []
        branche_name = text.strip()
        valid_branchs = {"塩路支店": "001", "メガネ支店": "002","バナナ支店": "003", "ボラ部支店": "004", "ゴリラ支店": "005", "マッコリ支店": "006", "ビースト支店": "810"}
        branche_num = valid_branches[branche_name]
        if branche_name in list(valid_branches.keys()):
            sessions[user_id]["branche_num"] = branche_num
            sessions[user_id]["step"] = 4
            messages.append(TextSendMessage(text=f"ご入力ありがとうございます。\n支店名:{branche_name}、支店番号{branche_num}で承りました。"))
            messages.append(TextSendMessage(text="次に、ご自身の希望する口座種別を、普通預金・定期預金からお選び下さい。"))
        else:
            messages.append(TextSendMessage(text="申し訳ありません。\n選択された支店名が正しくありません。\n再度確認の上、必ず支店名をご入力下さい。"))
        line_bot_api.reply_message(event.reply_token, messages)
    elif current_step == 4:
        account_type = text.strip()
        valid_account_types = ["普通預金", "定期預金"]
        if account_type in valid_account_types:
            # セッションに口座種別を保存
            sessions[user_id]["account_type"] = account_type
            sessions[user_id]["step"] = 5

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text=f"{display_name} 様、口座種別「{account_type}」で承りました。"),
                TextSendMessage(text="最後に、4桁の暗証番号を設定してください。(例:1234)\nまた、セキュリティの観点から、ご自身の誕生日や連続した数字、同じ数字の繰り返しは避けてください.")]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ございません。選択された口座種別が正しくありません。\n普通預金・当座預金・定期預金からお選びください。")
            )
        return
    elif current_step == 5:
        pin_code = text.strip()
        if pin_code.isdigit() and len(pin_code) == 4:
            # セッションに暗証番号を保存
            sessions[user_id]["pin_code"] = pin_code

            # account_creationに顧客情報を送信してアカウント作成を実行
            account_info = {
                "user_id": user_id,
                "full_name": sessions[user_id].get("full_name"),
                "birth_date": sessions[user_id].get("birth_date"),
                "account_type": sessions[user_id].get("account_type"),
                "pin_code": pin_code,
                "display_name": display_name
            }

            # account_creationを呼び出す
            create_account(event, account_info, sessions, user_id)

            # セッションをクリア
            sessions.pop(user_id, None)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ございません。暗証番号は4桁の数字で設定してください。(例:1234)")
            )
        return
