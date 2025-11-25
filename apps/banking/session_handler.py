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

    # ミニゲーム口座登録処理（個別チャットのみ）
    if text == "?ミニゲーム口座登録" or (isinstance(state, dict) and state.get("minigame_registration")):
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム口座登録は個別チャット(1対1トーク)でのみ利用可能です。"))
            return

        # キャンセル処理（どのステップでも優先して判定）
        if text.strip().lower() in ["?キャンセル", "?cancel"]:
            sessions.pop(user_id, None)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム用口座の登録をキャンセルしました。"))
            return

        # セッション管理: ミニゲーム口座登録フロー
        if text == "?ミニゲーム口座登録":
            # 現在の口座情報を取得
            minigame_info = bank_service.get_minigame_account_info(user_id)

            messages = []
            messages.append("【ミニゲーム口座登録】\n\n")
            messages.append("お持ちの口座をミニゲーム専用口座として登録します。\n")

            if minigame_info:
                messages.append(f"現在登録中のミニゲーム口座:\n支店番号: {minigame_info.get('branch_code')}\n口座番号: {minigame_info.get('account_number')}\n残高: {minigame_info.get('balance')} {minigame_info.get('currency')}\n\n")
                messages.append("別の口座に切り替える場合は、本人確認のため以下の情報を順番に入力してください。\n\n")
            else:
                messages.append("ミニゲーム用口座が未登録です。\n")
                messages.append("本人確認のため、以下の情報を順番に入力してください。\n\n")

            messages.append("まず、登録したい口座の支店番号（3桁）を入力してください。\n")
            messages.append("例: 001\n\n")
            messages.append("※「?口座情報」マンドで確認できます。\n")
            messages.append("※キャンセルする場合は「?キャンセル」と入力してください。")

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="".join(messages)))

            # セッションに状態を保存（ステップ1: 支店番号入力）
            sessions[user_id] = {"minigame_registration": True, "step": 1}
            return

        elif isinstance(state, dict) and state.get("minigame_registration"):
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
                    TextSendMessage(text=f"支店番号: {branch_code}\n\n次に、登録したい口座の口座番号（7桁）を入力してください。\n\n※「?口座情報」コマンドで確認できます。")
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
                    TextSendMessage(text=f"口座番号: {account_number}\n\n次に、口座開設時に登録したフルネームをカタカナで入力してください。\n例: ホンダ ハルキ")
                )
                return

            # ステップ3: 氏名入力
            elif current_step == 3:

                full_name = text.strip()
                import re

                # 全角カタカナが含まれているかチェック
                has_zen_kana = re.search(r'[ァ-ンヴー]', full_name)
                # 半角カタカナが含まれているかチェック
                has_han_kana = re.search(r'[ｦ-ﾟ]', full_name)

                # 全角カタカナが含まれていた場合は半角カナに変換
                if has_zen_kana:
                    # 半角カナ変換（unicodedata.normalizeは直接変換できないため、外部ライブラリ使用推奨だが、ここでは簡易変換）
                    try:
                        import jaconv
                        full_name = jaconv.z2h(full_name, kana=True, digit=False, ascii=False)
                    except ImportError:
                        # jaconvがない場合は警告
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="全角カタカナが含まれていましたが、半角カナへの変換に失敗しました。jaconvライブラリをインストールしてください。\n例: pip install jaconv")
                        )
                        return

                # カタカナチェック（半角カナまたは全角カナのみ許可）
                is_katakana = re.match(r'^[ｦ-ﾟ\s]+$', full_name)
                if not is_katakana or len(full_name.split(" ")) < 2:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="フルネームは半角カナで、苗字と名前の間にスペースを入れて入力してください。\n例: ﾎﾝﾀﾞ ﾊﾙｷ")
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

                result = bank_service.register_minigame_account(
                    user_id=user_id,
                    full_name=full_name,
                    branch_code=branch_code,
                    account_number=account_number,
                    pin_code=pin_code,
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

    # 口座開設中のやり取り
    elif current_step == 1 and not text.startswith("?") and text.strip() != "?キャンセル":
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
