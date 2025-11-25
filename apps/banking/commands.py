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
    
    # ユーザーに紐づく全口座を取得
    accounts = banking_api.get_accounts_by_user(user_id)
    
    if not accounts or len(accounts) == 0:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="有効な口座が見つかりません。「?口座開設」 を入力して口座を作成してください。"))
        return
    
    # 口座が1つの場合: 直接取引履歴を表示
    if len(accounts) == 1:
        account = accounts[0]
        branch_code = account.get('branch_code')
        account_number = account.get('account_number')
        
        _display_transaction_history(event, account_number, branch_code)
        return
    
    # 口座が複数の場合: 口座選択UIを表示
    from apps.help_flex import get_account_flex_bubble
    
    bubbles = []
    for acc in accounts:
        bubble = get_account_flex_bubble(acc)
        
        # ボタンを追加（通帳表示用）
        footer = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "この口座の通帳を見る",
                        "data": f"action=view_passbook&branch_code={acc.get('branch_code')}&account_number={acc.get('account_number')}"
                    },
                    "style": "primary",
                    "color": "#1E90FF"
                }
            ],
            "paddingAll": "12px"
        }
        bubble["footer"] = footer
        bubbles.append(bubble)
    
    flex_message = FlexSendMessage(
        alt_text="通帳を表示する口座を選択してください",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)


def _display_transaction_history(event, account_number, branch_code):
    """取引履歴をカルーセル形式で表示（内部関数）"""
    txs = banking_api.get_transactions(account_number, branch_code, limit=20)
    
    if not txs:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="この口座の取引履歴が見つかりません。"))
        return
    
    # 5件ずつ分割してカルーセル表示
    def chunk_list(lst, n):
        return [lst[i:i+n] for i in range(0, len(lst), n)]
    
    pages = chunk_list(txs, 5)
    
    bubbles = []
    for page_idx, page in enumerate(pages):
        items = []
        for tx in page:
            dt = tx.get('executed_at')
            try:
                dt_str = dt.strftime('%Y/%m/%d %H:%M') if dt else '-'
            except Exception:
                dt_str = str(dt) if dt else '-'
            
            items.append({
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": dt_str, "size": "xs", "color": "#999999"},
                    {"type": "text", "text": f"{tx.get('direction')} {tx.get('amount')} {tx.get('currency')}", 
                     "weight": "bold", "size": "md", "color": "#333333"},
                    {"type": "text", "text": f"相手口座: {tx.get('other_account_number') or '-'}", 
                     "size": "sm", "color": "#666666"},
                    {"type": "text", "text": f"種別: {tx.get('type') or '-'}", 
                     "size": "sm", "color": "#666666"},
                ],
                "paddingAll": "8px",
                "backgroundColor": "#F5F5F5",
                "cornerRadius": "4px"
            })
        
        bubble = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "通帳", "weight": "bold", "size": "xl", "color": "#1E90FF"},
                            {"type": "text", "text": f"{page_idx+1}/{len(pages)}", 
                             "size": "sm", "color": "#999999", "align": "end"}
                        ]
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "box", "layout": "vertical", "margin": "md", "spacing": "sm", "contents": items}
                ],
                "paddingAll": "18px"
            }
        }
        bubbles.append(bubble)
    
    carousel = {
        "type": "carousel",
        "contents": bubbles
    }
    
    flex_msg = FlexSendMessage(alt_text="通帳履歴", contents=carousel)
    line_bot_api.reply_message(event.reply_token, flex_msg)


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


def handle_passbook_postback(event, data):
    """通帳表示のpostbackアクション処理"""
    # dataから口座情報を抽出
    # 形式: "action=view_passbook&branch_code=001&account_number=1234567"
    import urllib.parse
    
    params = {}
    for param in data.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = urllib.parse.unquote(value)
    
    if params.get('action') == 'view_passbook':
        branch_code = params.get('branch_code')
        account_number = params.get('account_number')
        
        if branch_code and account_number:
            _display_transaction_history(event, account_number, branch_code)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="口座情報の取得に失敗しました。"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="不明なアクションです。"))
