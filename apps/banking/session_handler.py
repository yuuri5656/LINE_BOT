from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import datetime
from apps.banking.account_creation import create_account
from apps.banking import bank_service

def bank_reception(event, text, user_id, display_name, sessions):
    state = sessions.get(user_id)

    # 口座開設ステップ管理
    if isinstance(state, dict):
        current_step = state.get("step")
    else:
        current_step = None

    # ステップ別のメッセージテンプレート
    step_messages = {
        1: TextSendMessage(text="ご自身のフルネームを半角カタカナで教えてください。\n苗字と名前の間には半角スペースを挿入してください。(例:ﾎﾝﾀﾞ ﾊﾙｷ)"),
        2: TextSendMessage(text="ご自身の生年月日を「YYYY-MM-DD」の形式で教えてください。(例:2011-03-25)"),
        3: TextSendMessage(text="ご自身の希望する支店を以下から支店名でお選び下さい。\n※どの支店を選んで頂いてもご利用に影響はございません。\n\n支店名　　　　支店番号\n塩路支店　　　001\nメガネ支店　　002\nバナナ支店　　003\nボラ部支店　　004\nゴリラ支店　　005\nマッコリ支店　006\nビースト支店　810"),
        4: TextSendMessage(text="ご自身の希望する口座種別を、普通預金・当座預金・定期預金からお選び下さい。"),
        5: TextSendMessage(text="最後に、4桁の暗証番号を設定してください。(例:1234)\nまた、セキュリティの観点から、ご自身の誕生日や連続した数字、同じ数字の繰り返しは避けてください。")
    }
    # ?通帳コマンドは commands.py に統合されているため、ここでは処理しない
    # （このセクションは削除可能だが、念のためコメントとして残す）
    if text.strip() == "?通帳":
        # commands.pyのhandle_passbookで処理されるため、ここには到達しない
        # もし到達した場合は呼び出し元の実装エラー
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="通帳コマンドの処理に問題がありました。管理者にご連絡ください。"))
        return

    # "?戻る"の処理
    if text == "?戻る" and isinstance(state, dict) and state.get("step"):
        current_step_num = state.get("step")
        if current_step_num > 1:
            # 前のステップに戻る
            prev_step = current_step_num - 1
            state["step"] = prev_step

            # step_messagesに該当するメッセージがない場合は複数メッセージで返す
            if prev_step == 3:
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="ご自身の希望する支店を以下から支店名でお選び下さい。\n※どの支店を選んで頂いてもご利用に影響はございません。"),
                    TextSendMessage(text="支店名　　　　支店番号\n塩路支店　　　001\nメガネ支店　　002\nバナナ支店　　003\nボラ部支店　　004\nゴリラ支店　　005\nマッコリ支店　006\nビースト支店　810")]
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    step_messages[prev_step]
                )
            return

    # 口座開設の初期化処理
    if text.strip() == "?口座開設":
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="口座開設は個別チャット(1対1トーク)でのみ利用可能です。"))
            return

        # セッションを初期化してステップ1を開始
        sessions[user_id] = {"step": 1}
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=f"{display_name} 様、ようこそ！\n口座開設のお手続きを開始いたします。"),
                TextSendMessage(text="ご自身のフルネームを半角カタカナで教えてください。\n苗字と名前の間には半角スペースを挿入してください。(例:ﾎﾝﾀﾞ ﾊﾙｷ)")
            ]
        )
        return

    # ミニゲーム口座登録処理（個別チャットのみ）- 口座選択方式に変更
    if text == "?ミニゲーム口座登録":
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム口座登録は個別チャット(1対1トーク)でのみ利用可能です。"))
            return

        # 銀行口座を取得
        bank_accounts = banking_api.get_accounts_by_user(user_id)

        if not bank_accounts or len(bank_accounts) == 0:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="銀行口座が見つかりません。先に「?口座開設」で銀行口座を作成してください。")
            )
            return

        # ミニゲーム口座機能は廃止されました
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ミニゲーム口座機能は廃止されました。\n現在はチップシステムをご利用ください。\n\nコマンド: ?ショップ")
        )
        return

    # ミニゲーム口座登録セッション処理（廃止済み）
    if isinstance(state, dict) and state.get("minigame_registration"):
        # ミニゲーム口座機能は廃止されたため、セッションをクリア
        sessions.pop(user_id, None)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ミニゲーム口座機能は廃止されました。\n現在はチップシステムをご利用ください。\n\nコマンド: ?ショップ")
        )
        return

    # キャンセルコマンドの優先チェック（全ステップ共通）
    if text.strip() == "?キャンセル" and isinstance(state, dict) and state.get("step"):
        sessions.pop(user_id, None)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="口座開設をキャンセルしました。"))
        return

    # 口座開設中のやり取り
    elif current_step == 1 and not text.startswith("?"):
        full_name = text.strip()
        import re
        # 全角カタカナ→半角カタカナ変換関数
        def zen_to_han_kana(s):
            import unicodedata
            # Unicode正規化で半角カナに変換
            s = unicodedata.normalize('NFKC', s)
            # 半角カナ以外はそのまま
            return s
        # 半角カタカナか全角カタカナか判定
        is_hankaku = re.match(r'^[ｦ-ﾟ ]+$', full_name)
        is_zenkaku = re.match(r'^[ァ-ヶー　]+$', full_name)
        if len(full_name.split(" ")) >= 2 and (is_hankaku or is_zenkaku):
            # 全角カタカナの場合は半角カタカナに変換
            if is_zenkaku:
                full_name_hankaku = zen_to_han_kana(full_name.replace('　', ' '))
            else:
                full_name_hankaku = full_name
            messages = []
            if not isinstance(sessions.get(user_id), dict):
                sessions[user_id] = {"step": 2, "full_name": full_name_hankaku}
            else:
                sessions[user_id]["full_name"] = full_name_hankaku
                sessions[user_id]["step"] = 2
            messages.append(TextSendMessage(text=f"{display_name} 様、ありがとうございます。\n「{full_name_hankaku} 様」で登録させて頂きます。"))
            messages.append(TextSendMessage(text="次に、ご自身の生年月日を「YYYY-MM-DD」の形式で教えてください。(例:2011-03-25)"))
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ございません。フルネームはカタカナで入力してください。\n苗字と名前の間にスペースを挿入してください。(例:ﾔﾏﾀﾞ ﾀﾛｳ または ヤマダ タロウ)")
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
        branch_name = text.strip()
        valid_branches = {"塩路支店": "001", "メガネ支店": "002","バナナ支店": "003", "ボラ部支店": "004", "ゴリラ支店": "005", "マッコリ支店": "006", "ビースト支店": "810"}
        branch_num = valid_branches[branch_name]
        if branch_name in list(valid_branches.keys()):
            sessions[user_id]["branch_num"] = branch_num
            sessions[user_id]["step"] = 4
            messages.append(TextSendMessage(text=f"ご入力ありがとうございます。\n支店名:{branch_name}、支店番号{branch_num}で承りました。"))
            messages.append(TextSendMessage(text="次に、ご自身の希望する口座種別を、普通預金・当座預金・定期預金からお選び下さい。"))
        else:
            messages.append(TextSendMessage(text="申し訳ありません。\n選択された支店名が正しくありません。\n再度確認の上、必ず支店名をご入力下さい。"))
        line_bot_api.reply_message(event.reply_token, messages)
    elif current_step == 4:
        account_type = text.strip()
        valid_account_types = ["普通預金", "定期預金", "当座預金"]
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
                "branch_num": sessions[user_id].get("branch_num"),
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
