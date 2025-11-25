"""
メッセージルーティングモジュール
コマンドを適切なハンドラーに振り分ける
"""
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from core.api import line_bot_api
from apps.help_flex import get_detail_account_flex, get_detail_minigame_flex, get_detail_janken_flex

# 各機能のコマンドハンドラーをインポート
from apps.banking import commands as banking_commands
from apps.games import commands as game_commands
from apps.utilities import commands as utility_commands


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
        elif data == "help_detail_minigame":
            line_bot_api.reply_message(event.reply_token, get_detail_minigame_flex())
            return
        elif data == "help_detail_janken":
            line_bot_api.reply_message(event.reply_token, get_detail_janken_flex())
            return
        # 通帳表示のpostbackアクション
        elif data.startswith("action=view_passbook"):
            banking_commands.handle_passbook_postback(event, data)
            return
    
    state = sessions.get(user_id)
    
    # === 銀行機能（個別チャット） ===
    if event.source.type == 'user':
        # 口座開設・ミニゲーム口座登録フロー中の処理
        if isinstance(state, dict) and (state.get("step") or state.get("minigame_registration")):
            # セッション中に新たな開始コマンドが来た場合は拒否
            if text.strip() in ["?口座開設", "?ミニゲーム口座登録"]:
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
        
        if text.strip() == "?ミニゲーム口座登録":
            banking_commands.handle_minigame_registration(event, text, user_id, display_name, sessions)
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
