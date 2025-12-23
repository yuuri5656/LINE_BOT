"""
メッセージルーティングモジュール
コマンドを適切なハンドラーに振り分ける
"""
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from core.api import line_bot_api
from apps.help_flex import get_detail_account_flex, get_detail_janken_flex, get_detail_shop_flex, get_detail_stock_flex, get_detail_utility_flex

# 各機能のコマンドハンドラーをインポート
from apps.banking import commands as banking_commands
from apps.banking.api import banking_api
from apps.games import commands as game_commands
from apps.utilities import commands as utility_commands
from apps.shop import commands as shop_commands
from apps.stock import commands as stock_commands
from apps.work import commands as work_commands
from apps.prison import commands as prison_commands
from apps.prison import prison_service
from apps.rich_menu import menu_manager


def auto_reply(event, text, user_id, group_id, display_name, sessions):
    """
    メッセージを受け取り、適切なコマンドハンドラーに振り分ける
    """
    # Postbackイベントで詳細ヘルプを返す
    if hasattr(event, 'postback') and event.postback and hasattr(event.postback, 'data'):
        data = event.postback.data
        
        # リッチメニューページ切り替え
        if data.startswith("action=richmenu_page"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            page = parsed_data.get("page", "1-1")  # 例: "1-1", "2-2"
            menu_manager.switch_user_menu(user_id, page)
            return
        
        # リッチメニューからの各種アクション
        # 口座開設
        elif data == "action=account_create":
            banking_commands.handle_account_opening(event, "?口座開設", user_id, display_name, sessions)
            return
        # 通帳
        elif data == "action=passbook":
            banking_commands.handle_passbook(event, user_id)
            return
        # 振り込み
        elif data == "action=transfer":
            banking_commands.handle_transfer(event, user_id, sessions)
            return
        # ショップホーム
        elif data == "action=shop_home":
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                response = shop_commands.handle_shop_command(user_id, db)
                line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return
        # チップ残高
        elif data == "action=chip_balance":
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                response = shop_commands.handle_chip_balance_command(user_id, db)
                line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return
        # チップ換金（リッチメニュー用）
        elif data == "action=chip_exchange":
            from apps.banking.main_bank_system import get_db
            from apps.shop.shop_flex import get_chip_exchange_flex
            db = next(get_db())
            try:
                chip_balance = shop_commands.get_user_chip_balance(user_id, db)
                line_bot_api.reply_message(
                    event.reply_token,
                    get_chip_exchange_flex(chip_balance)
                )
            finally:
                db.close()
            return
        # チップ全額換金
        elif data == "action=chip_exchange_all":
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                response = shop_commands.handle_chip_exchange_all(user_id, db)
                line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return
        # チップ一覧（ショップFlexMessage）
        elif data == "action=chip_list":
            from apps.banking.main_bank_system import get_db
            db = next(get_db())
            try:
                response = shop_commands.handle_shop_command(user_id, db)
                line_bot_api.reply_message(event.reply_token, response)
            finally:
                db.close()
            return
        # 株式ダッシュボード
        elif data == "action=stock_home":
            stock_commands.handle_stock_command(event, user_id)
            return
        # 銘柄一覧
        elif data == "action=stock_list":
            stock_commands.handle_stock_list(event, user_id)
            return
        # ゲームメニュー
        elif data == "action=game_home":
            game_commands.handle_game_menu(event, user_id)
            return
        # おみくじ
        elif data == "action=omikuji":
            utility_commands.handle_omikuji(event, user_id, display_name, "?おみくじ")
            return
        # 明日の時間割
        elif data == "action=timetable":
            utility_commands.handle_timetable(event)
            return
        # 労働
        elif data == "action=work_home":
            work_commands.handle_work_command(event, user_id)
            return
        elif data == "action=help_home":
            utility_commands.handle_help(event)
            return

        # === 税/借金 (Flex) ===
        elif data.startswith("action=tax_") or data.startswith("action=loan_"):
            import urllib.parse
            parsed = dict(urllib.parse.parse_qsl(data))
            action = parsed.get('action')

            # 税
            if action and action.startswith('tax_'):
                from apps.tax.ui import handle_tax_postback
                resp = handle_tax_postback(action=action, parsed=parsed, user_id=user_id, sessions=sessions)
                if resp:
                    line_bot_api.reply_message(event.reply_token, resp)
                return

            # 借金
            if action and action.startswith('loan_'):
                from apps.loans.ui import handle_loan_postback
                resp = handle_loan_postback(action=action, parsed=parsed, user_id=user_id, sessions=sessions)
                if resp:
                    line_bot_api.reply_message(event.reply_token, resp)
                return
        
        # 既存のヘルプ詳細 (action=プレフィックス対応)
        if data == "action=help_detail_account" or data == "help_detail_account":
            line_bot_api.reply_message(event.reply_token, get_detail_account_flex())
            return
        elif data == "action=help_detail_janken" or data == "help_detail_janken" or data == "action=help_detail_game":
            line_bot_api.reply_message(event.reply_token, get_detail_janken_flex())
            return
        elif data == "action=help_detail_shop" or data == "help_detail_shop":
            line_bot_api.reply_message(event.reply_token, get_detail_shop_flex())
            return
        elif data == "action=help_detail_stock" or data == "help_detail_stock":
            line_bot_api.reply_message(event.reply_token, get_detail_stock_flex())
            return
        elif data == "action=help_detail_utility" or data == "help_detail_utility":
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
        elif data.startswith("action=shop_") or data.startswith("action=confirm_shop_payment_account") or data.startswith("action=select_shop_payment_account"):
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
        # 株式のpostbackアクション
        elif data.startswith("action=stock_") or data.startswith("action=confirm_stock_") or data.startswith("action=buy_stock") or data.startswith("action=sell_stock") or data.startswith("action=confirm_buy") or data.startswith("action=confirm_sell") or data.startswith("action=cancel_trade") or data.startswith("action=my_holdings") or data.startswith("action=market_news") or data.startswith("action=select_stock_account"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            stock_commands.handle_stock_postback(event, parsed_data, user_id)
            return
        # 労働システムのpostbackアクション
        elif data.startswith("action=select_work_salary_account") or data.startswith("action=confirm_work_salary_account"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            work_commands.handle_work_postback(event, parsed_data, user_id)
            return
        # 個別ゲームのpostbackアクション
        elif data.startswith("action=select_game"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            game_commands.handle_game_selection(event, user_id, parsed_data)
            return
        elif data.startswith("action=add_bet"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            game_commands.handle_add_bet(event, user_id, parsed_data)
            return
        elif data.startswith("action=reset_bet"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            game_commands.handle_reset_bet(event, user_id, parsed_data)
            return
        elif data.startswith("action=confirm_bet"):
            import urllib.parse
            parsed_data = dict(urllib.parse.parse_qsl(data))
            game_commands.handle_confirm_bet(event, user_id, parsed_data)
            return
        elif data in ["action=hit", "action=stand", "action=double"]:
            action = data.split('=')[1]
            game_commands.handle_blackjack_action(event, user_id, action)
            return

    state = sessions.get(user_id)

    # === 回収（督促）の割り込み ===
    # 全発言に対して督促文をpushで送る（返信枠を消費しない）
    if event.source.type == 'user':
        try:
            from apps.collections.collections_service import get_inline_notice_text
            notice = get_inline_notice_text(user_id)
            if notice:
                line_bot_api.push_message(user_id, TextSendMessage(text=notice))
        except Exception as e:
            print(f"[AutoReply] inline notice push failed user={user_id} err={e}")

    # === 懲役中ユーザーの制限チェック ===
    prisoner_status = prison_service.get_prisoner_status(user_id)
    if prisoner_status['is_imprisoned']:
        # 懲役中のユーザーは?労働のみを許可
        if text != "?労働" and not text.startswith("?キャンセル"):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 懲役中のため、?労働のみが実行可能です")
            )
            return

    # === 税/借金: テキスト入力フロー（PIN/金額など） ===
    if event.source.type == 'user' and isinstance(state, dict) and state.get('flex_flow'):
        from apps.tax.ui import handle_tax_text_flow
        from apps.loans.ui import handle_loan_text_flow

        resp = handle_tax_text_flow(text=text, user_id=user_id, sessions=sessions)
        if resp:
            line_bot_api.reply_message(event.reply_token, resp)
            return

        resp = handle_loan_text_flow(text=text, user_id=user_id, sessions=sessions)
        if resp:
            line_bot_api.reply_message(event.reply_token, resp)
            return

    # === ?コマンドの優先処理（セッション中でも実行可能） ===
    # キャンセルコマンド（最優先）
    if text.strip() == "?キャンセル":
        # 銀行セッションのキャンセル
        if isinstance(state, dict) and (state.get("step") or state.get("transfer")):
            if state.get("transfer"):
                if banking_commands.handle_transfer_cancel(event, user_id, sessions):
                    return
            elif state.get("step"):
                if banking_commands.handle_cancel(event, user_id, sessions):
                    return
        # ゲームセッションのキャンセル
        if event.source.type == 'group':
            if game_commands.handle_game_cancel(event, user_id, group_id):
                return

    # その他の?コマンド（セッション中でも実行可能）
    if text == "?userid":
        utility_commands.handle_userid(event, user_id)
        return

    if text in ["?ヘルプ", "?help"]:
        utility_commands.handle_help(event)
        return

    # リッチメニュー管理コマンド
    if text == "?メニュー作成":
        from apps.rich_menu import commands as richmenu_commands
        richmenu_commands.handle_menu_create(event)
        return

    if text == "?メニュー削除":
        from apps.rich_menu import commands as richmenu_commands
        richmenu_commands.handle_menu_delete(event)
        return

    if text == "?メニュー状態":
        from apps.rich_menu import commands as richmenu_commands
        richmenu_commands.handle_menu_status(event)
        return

    if text == "?口座情報":
        banking_commands.handle_account_info(event, user_id)
        return

    if text == "?通帳":
        banking_commands.handle_passbook(event, user_id)
        return

    if text == "?株":
        stock_commands.handle_stock_command(event, user_id)
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

    # === 税/借金 ===
    if text.strip() == "?税":
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="税は個別チャットで利用してください"))
            return
        from apps.tax.ui import build_dashboard
        line_bot_api.reply_message(event.reply_token, build_dashboard(user_id))
        return

    if text.strip() == "?借金":
        if event.source.type != 'user':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="借金は個別チャットで利用してください"))
            return
        from apps.loans.ui import build_dashboard
        line_bot_api.reply_message(event.reply_token, build_dashboard(user_id))
        return

    if text.startswith("?納税"):
        from apps.tax.commands import handle_tax_command
        line_bot_api.reply_message(event.reply_token, handle_tax_command(user_id, text))
        return

    if text.startswith("?借入"):
        from apps.loans.commands import handle_loan_command
        line_bot_api.reply_message(event.reply_token, handle_loan_command(user_id, text))
        return

    if text.startswith("?返済"):
        from apps.loans.commands import handle_loan_command
        line_bot_api.reply_message(event.reply_token, handle_loan_command(user_id, text))
        return

    if text == "?ゲーム":
        game_commands.handle_game_menu(event, user_id)
        return

    # === 銀行機能（個別チャット） ===
    if event.source.type == 'user':
        # 株式トレードセッション中の処理
        from apps.stock.api import stock_api
        if stock_api.has_session(user_id):
            if stock_commands.handle_stock_session(event, user_id, text.strip()):
                return

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
            # セッション中の入力処理
            banking_commands.handle_transfer_session_input(event, text, user_id, sessions)
            return

        # 口座開設フロー中の処理
        if isinstance(state, dict) and state.get("step"):
            # セッション中に新たな開始コマンドが来た場合は拒否
            if text.strip() in ["?口座開設", "?振り込み"]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="現在登録フロー中です。キャンセルまたは完了後に再度お試しください。"))
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

    if text in ["?ヘルプ", "?help"]:
        utility_commands.handle_help(event)
        return

    if text == "?アップデート":
        from apps.help_flex import get_update_announcement_flex
        line_bot_api.reply_message(event.reply_token, get_update_announcement_flex())
        return

    if text == "?口座情報":
        banking_commands.handle_account_info(event, user_id)
        return

    if text == "?通帳":
        banking_commands.handle_passbook(event, user_id)
        return

    # === セッションが必要なコマンド（個別チャット） ===
    if event.source.type == 'user':
        if text == "?振り込み":
            banking_commands.handle_transfer(event, user_id, sessions)
            return

        if text == "?チップ送受信":
            banking_commands.handle_chip_transfer(event, user_id, sessions)
            return

        # チップ送受信セッション中の処理
        if isinstance(state, dict) and state.get("chip_transfer"):
            banking_commands.handle_chip_transfer_session_input(event, text, user_id, sessions)
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

    if text == "?労働":
        work_commands.handle_work_command(event, user_id)
        return

    # === 管理者コマンド ===
    if text.startswith("?ユーザー口座 "):
        if not prison_commands.is_admin(user_id):
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です"))
            return
        target_user_id = text.replace("?ユーザー口座 ", "").strip()
        prison_commands.handle_admin_user_accounts(event, user_id, target_user_id)
        return

    if text.startswith("?口座番号 "):
        if not prison_commands.is_admin(user_id):
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です"))
            return
        account_number = text.replace("?口座番号 ", "").strip()
        prison_commands.handle_admin_account_number(event, user_id, account_number)
        return

    if text.startswith("?懲役 "):
        if not prison_commands.is_admin(user_id):
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です"))
            return
        # パース: "?懲役 [user_id] [start_date] [days] [quota]"
        params = text.replace("?懲役 ", "").split()
        if len(params) < 4:
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ 形式: ?懲役 [user_id] [施行日(YYYY-MM-DD)] [日数] [ノルマ]"))
            return
        prison_commands.handle_admin_sentence(event, user_id, params[0], params[1], int(params[2]), int(params[3]))
        return

    if text.startswith("?凍結 "):
        if not prison_commands.is_admin(user_id):
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です"))
            return
        account_number = text.replace("?凍結 ", "").strip()
        prison_commands.handle_admin_freeze_account(event, user_id, account_number)
        return

    if text.startswith("?釈放 "):
        if not prison_commands.is_admin(user_id):
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です"))
            return
        target_user_id = text.replace("?釈放 ", "").strip()
        prison_commands.handle_admin_release(event, user_id, target_user_id)
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

        if text == "?開始":
            game_commands.handle_game_start(event, user_id, group_id)
            return

    # === デフォルト応答 ===
    if event.source.type == 'user':
        utility_commands.handle_default_user_message(event)
