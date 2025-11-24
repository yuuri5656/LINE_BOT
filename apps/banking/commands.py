"""
銀行機能関連のコマンドハンドラー
"""
from linebot.models import TextSendMessage, FlexSendMessage
from core.api import line_bot_api
from apps.banking.api import banking_api
from apps.banking.session_handler import bank_reception


def handle_account_opening(event, text, user_id, display_name, sessions):
    """口座開設コマンド"""
    bank_reception(event, text, user_id, display_name, sessions)


def handle_minigame_registration(event, text, user_id, display_name, sessions):
    """ミニゲーム口座登録コマンド"""
    bank_reception(event, text, user_id, display_name, sessions)


def handle_account_info(event, user_id):
    """口座情報表示コマンド"""
    if event.source.type != 'user':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="個別チャットでのみ利用可能です。塩爺に直接メッセージを送ってください。"))
        return
    
    from apps.help_flex import get_account_flex_bubble
    accounts = banking_api.get_accounts_by_user(user_id)
    
    if not accounts or not isinstance(accounts, list) or len(accounts) == 0:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="有効な口座が見つかりません。「?口座開設」 を入力して口座を作成してください。"))
        return
    
    bubbles = [get_account_flex_bubble(acc) for acc in accounts if acc]
    if not bubbles:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="口座情報の取得に失敗しました。管理者にご連絡ください。"))
        return
    
    flex_message = FlexSendMessage(
        alt_text="口座情報一覧",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)


def handle_passbook(event, user_id):
    """通帳（取引履歴）表示コマンド"""
    if event.source.type != 'user':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="個別チャットでのみ利用可能です。塩爺に直接メッセージを送ってください。"))
        return
    
    txs = banking_api.get_transactions(user_id, limit=20)
    if not txs:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="取引履歴が見つかりません。"))
        return
    
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


def handle_cancel(event, user_id, sessions):
    """キャンセルコマンド（銀行セッション用）"""
    state = sessions.get(user_id)
    if isinstance(state, dict):
        if state.get("step"):
            state.pop("step", None)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="口座開設をキャンセルしました。"))
            return True
        if state.get("minigame_registration"):
            state.pop("minigame_registration", None)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ミニゲーム口座登録をキャンセルしました。"))
            return True
    return False


def handle_back(event, text, user_id, display_name, sessions):
    """戻るコマンド（銀行セッション用）"""
    bank_reception(event, text, user_id, display_name, sessions)


def handle_session_input(event, text, user_id, display_name, sessions):
    """セッション中の入力処理"""
    bank_reception(event, text, user_id, display_name, sessions)
