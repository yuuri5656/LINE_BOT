"""
メッセージルーティングモジュール
コマンドを適切なハンドラーに振り分ける
"""
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from core.api import line_bot_api
from apps.help_flex import get_detail_account_flex, get_detail_janken_flex, get_detail_shop_flex, get_detail_utility_flex

# 各機能のコマンドハンドラーをインポート
from apps.banking import commands as banking_commands
from apps.games import commands as game_commands
from apps.utilities import commands as utility_commands
from apps.shop import commands as shop_commands


def auto_reply(event, text, user_id, group_id, display_name, sessions):
    """
    メッセージを受け取り、適切なコマンドハンドラーに振り分ける
    """
    # Postbackイベントで詳細ヘルプを返す
    if hasattr(event, 'postback') and event.postback and hasattr(event.postback, 'data'):
        data = event.postback.data
        if data == "help_detail_account":
            line_bot_api.reply_message(event.reply_token, get_detail_account_flex())
            return
        elif data == "help_detail_janken":
            line_bot_api.reply_message(event.reply_token, get_detail_janken_flex())
            return
        elif data == "help_detail_shop":
            line_bot_api.reply_message(event.reply_token, get_detail_shop_flex())
            return
        elif data == "help_detail_utility":
            line_bot_api.reply_message(event.reply_token, get_detail_utility_flex())
            return
        # 通帳表示のpostbackアクション
        elif data.startswith("action=view_passbook"):
            banking_commands.handle_passbook_postback(event, data)
            return
        # 振り込み用口座選択のpostbackアクション
        elif data.startswith("action=select_transfer_account"):
            banking_commands.handle_transfer_account_selection_postback(event, data, user_id, sessions)
            return
        # じゃんけんゲームのpostbackアクション
        elif data == "action=join_janken":
            if event.source.type == 'group':
                game_commands.handle_join_game(event, user_id, display_name, group_id)
            return
        elif data == "action=start_janken":
            if event.source.type == 'group':
                game_commands.handle_game_start(event, user_id, group_id)
            return
        elif data == "action=cancel_janken":
            if event.source.type == 'group':
                game_commands.handle_game_cancel(event, user_id, group_id)
            return
        # ショップのpostbackアクション
        elif data.startswith("action=shop_") or data.startswith("action=register_payment_account"):
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                # postbackデータをパース
                import urllib.parse
                parsed_data = dict(urllib.parse.parse_qsl(data))
                # ショップpostback処理
                response = shop_commands.handle_shop_postback(user_id, parsed_data, db)
                if response:
                    line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return

    state = sessions.get(user_id)

    # === 銀行機能（個別チャット） ===
    if event.source.type == 'user':
        # ショップ支払い口座登録セッション中の処理
        from apps.shop.commands import shop_session_manager
        shop_state = shop_session_manager.get_session(user_id)
        if shop_state and shop_state.get('type') == 'payment_registration':
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                response = shop_commands.handle_payment_registration_session(user_id, text.strip(), db)
                if response:
                    line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return

        # 振り込みセッション中の処理
        if isinstance(state, dict) and state.get("transfer"):
            # キャンセルコマンド
            if text.strip() == "?キャンセル":
                if banking_commands.handle_transfer_cancel(event, user_id, sessions):
                    return

            # セッション中の入力処理
            banking_commands.handle_transfer_session_input(event, text, user_id, sessions)
            return

        # 口座開設フロー中の処理
        if isinstance(state, dict) and state.get("step"):
            # セッション中に新たな開始コマンドが来た場合は拒否
            if text.strip() in ["?口座開設", "?振り込み"]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="現在登録フロー中です。キャンセルまたは完了後に再度お試しください。"))
                return

            # キャンセルコマンド
            if text.strip() == "?キャンセル":
                if banking_commands.handle_cancel(event, user_id, sessions):
                    return

            # 戻るコマンド
            if text.strip() == "?戻る":
                banking_commands.handle_back(event, text, user_id, display_name, sessions)
                return

            # セッション中の入力処理
            banking_commands.handle_session_input(event, text, user_id, display_name, sessions)
            return

        # 新規開始コマンド
        if text.strip() == "?口座開設":
            banking_commands.handle_account_opening(event, text, user_id, display_name, sessions)
            return

        # プレイヤーの手入力（じゃんけん）
        if game_commands.handle_player_move(event, user_id, text):
            return

    # === 共通コマンド ===
    if text == "?userid":
        utility_commands.handle_userid(event, user_id)
        return

    if text in ["?ヘルプ", "?help"]:
        utility_commands.handle_help(event)
        return

    if text == "?口座情報":
        banking_commands.handle_account_info(event, user_id)
        return

    if text == "?通帳":
        banking_commands.handle_passbook(event, user_id)
        return

    if text == "?振り込み":
        banking_commands.handle_transfer(event, user_id, sessions)
        return

    # === ショップ機能 ===
    if text == "?ショップ":
        from apps.banking.main_bank_system import get_db
        db = next(get_db())
        try:
            response = shop_commands.handle_shop_command(user_id, db)
            line_bot_api.reply_message(event.reply_token, response)
        finally:
            db.close()
        return

    if text == "?チップ残高":
        from apps.banking.main_bank_system import get_db
        db = next(get_db())
        try:
            response = shop_commands.handle_chip_balance_command(user_id, db)
            line_bot_api.reply_message(event.reply_token, response)
        finally:
            db.close()
        return

    if text == "?チップ履歴":
        from apps.banking.main_bank_system import get_db
        db = next(get_db())
        try:
            response = shop_commands.handle_chip_history_command(user_id, db)
            line_bot_api.reply_message(event.reply_token, response)
        finally:
            db.close()
        return

    if text.startswith("?チップ換金"):
        from apps.banking.main_bank_system import get_db
        db = next(get_db())
        try:
            response = shop_commands.handle_chip_redeem_command(user_id, text, db)
            line_bot_api.reply_message(event.reply_token, response)
        finally:
            db.close()
        return

    if text == "?明日の時間割":
        utility_commands.handle_timetable(event)
        return

    if text == "?おみくじ":
        utility_commands.handle_omikuji(event, user_id, display_name, text)
        return

    if text.startswith("?RPN"):
        utility_commands.handle_rpn(event, text)
        return

    if text.startswith("?setname"):
        utility_commands.handle_setname(event, user_id, text)
        return

    # お遊びコマンド
    if utility_commands.handle_fun_commands(event, text):
        return

    # === ゲーム機能（グループチャット） ===
    if event.source.type == 'group':
        if text == "?じゃんけん":
            game_commands.handle_janken_start(event, user_id, text, display_name, group_id, sessions)
            return

        if text == "?参加":
            game_commands.handle_join_game(event, user_id, display_name, group_id)
            return

        if text == "?キャンセル":
            if game_commands.handle_game_cancel(event, user_id, group_id):
                return

        if text == "?開始":
            game_commands.handle_game_start(event, user_id, group_id)
            return

    # === デフォルト応答 ===
    if event.source.type == 'user':
        utility_commands.handle_default_user_message(event)
