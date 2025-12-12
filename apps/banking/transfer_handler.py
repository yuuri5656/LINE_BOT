"""
振り込み機能のセッション管理とハンドラー
"""
from linebot.models import TextSendMessage
from core.api import line_bot_api
from apps.banking.api import banking_api
from apps.banking.transfer_flex import (
    get_transfer_guide_flex,
    get_transfer_success_flex,
    get_transfer_error_flex,
    get_account_selection_flex
)
import datetime
from decimal import Decimal, InvalidOperation
from apps.utilities.timezone_utils import now_jst


def handle_transfer_command(event, user_id, sessions):
    """振り込みコマンドの処理

    Args:
        event: LINEイベントオブジェクト
        user_id: ユーザーID
        sessions: セッション辞書
    """
    # 個別チャット限定
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="振り込みは個別チャットでのみ利用可能です。塩爺に直接メッセージを送ってください。")
        )
        return

    # ユーザーの口座を取得
    accounts = banking_api.get_accounts_by_user(user_id)

    if not accounts or len(accounts) == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="有効な口座が見つかりません。「?口座開設」を入力して口座を作成してください。")
        )
        return

    # 口座が1つの場合: 直接振り込み手続きを開始
    if len(accounts) == 1:
        account = accounts[0]
        _start_transfer_session(event, user_id, sessions, account)
        return

    # 口座が複数の場合: 口座選択UIを表示
    flex_message = get_account_selection_flex(accounts)
    line_bot_api.reply_message(event.reply_token, flex_message)


def handle_account_selection_postback(event, data, user_id, sessions):
    """口座選択のpostback処理

    Args:
        event: LINEイベントオブジェクト
        data: postbackデータ
        user_id: ユーザーID
        sessions: セッション辞書
    """
    import urllib.parse

    # dataをパース
    params = {}
    for param in data.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = urllib.parse.unquote(value)

    if params.get('action') != 'select_transfer_account':
        return

    branch_code = params.get('branch_code')
    account_number = params.get('account_number')

    if not branch_code or not account_number:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="口座情報の取得に失敗しました。")
        )
        return

    # 選択された口座の情報を取得
    accounts = banking_api.get_accounts_by_user(user_id)
    selected_account = None
    for acc in accounts:
        if acc.get('branch_code') == branch_code and acc.get('account_number') == account_number:
            selected_account = acc
            break

    if not selected_account:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="選択された口座が見つかりません。")
        )
        return

    # 振り込み手続きを開始
    _start_transfer_session(event, user_id, sessions, selected_account)


def _start_transfer_session(event, user_id, sessions, from_account):
    """振り込みセッションを開始

    Args:
        event: LINEイベントオブジェクト
        user_id: ユーザーID
        sessions: セッション辞書
        from_account: 振込元口座情報
    """
    # セッションを初期化
    sessions[user_id] = {
        'transfer': {
            'step': 'branch_code',
            'from_account_number': from_account.get('account_number'),
            'from_branch_code': from_account.get('branch_code'),
            'from_balance': from_account.get('balance')
        }
    }

    # 案内メッセージを送信
    line_bot_api.reply_message(event.reply_token, get_transfer_guide_flex())


def handle_transfer_session_input(event, text, user_id, sessions):
    """振り込みセッション中の入力処理

    Args:
        event: LINEイベントオブジェクト
        text: 入力テキスト
        user_id: ユーザーID
        sessions: セッション辞書
    """
    session = sessions.get(user_id)
    if not session or 'transfer' not in session:
        return

    transfer_data = session['transfer']
    step = transfer_data.get('step')

    if step == 'branch_code':
        _handle_branch_code_input(event, text, user_id, sessions, transfer_data)
    elif step == 'account_number':
        _handle_account_number_input(event, text, user_id, sessions, transfer_data)
    elif step == 'amount':
        _handle_amount_input(event, text, user_id, sessions, transfer_data)
    elif step == 'pin':
        _handle_pin_input(event, text, user_id, sessions, transfer_data)


def _handle_branch_code_input(event, text, user_id, sessions, transfer_data):
    """支店コード入力処理"""
    # 3桁の数字チェック
    if not text.isdigit() or len(text) != 3:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="支店コードは3桁の数字で入力してください。\n例: 001")
        )
        return

    # 支店コードを保存して次のステップへ
    transfer_data['to_branch_code'] = text
    transfer_data['step'] = 'account_number'
    sessions[user_id]['transfer'] = transfer_data

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"支店コード: {text}\n\n次に、振込先の口座番号（7桁）を入力してください。")
    )


def _handle_account_number_input(event, text, user_id, sessions, transfer_data):
    """口座番号入力処理"""
    # 7桁の数字チェック
    if not text.isdigit() or len(text) != 7:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="口座番号は7桁の数字で入力してください。\n例: 1234567")
        )
        return

    # 振込先口座の存在確認
    to_branch_code = transfer_data.get('to_branch_code')
    from apps.banking.main_bank_system import SessionLocal, Account, Branch
    from sqlalchemy import select

    db = SessionLocal()
    try:
        # 支店を取得
        branch = db.execute(select(Branch).filter_by(code=to_branch_code)).scalars().first()
        if not branch:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex(
                    f"支店コード {to_branch_code} が見つかりません。",
                    'validation'
                )
            )
            # セッションをクリア
            sessions.pop(user_id, None)
            return

        # 口座を取得（active/frozenのみ、closedは除外）
        account = db.execute(
            select(Account).filter_by(
                account_number=text,
                branch_id=branch.branch_id
            )
        ).scalars().first()

        if not account or getattr(account, 'status', None) not in ('active', 'frozen'):
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex(
                    f"口座番号 {text} が見つからないか、利用できない状態です。",
                    'validation'
                )
            )
            # セッションをクリア
            sessions.pop(user_id, None)
            return

        # 自分自身への振り込みチェック
        from_account_number = transfer_data.get('from_account_number')
        from_branch_code = transfer_data.get('from_branch_code')
        if text == from_account_number and to_branch_code == from_branch_code:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex(
                    "自分自身の口座への振り込みはできません。",
                    'validation'
                )
            )
            # セッションをクリア
            sessions.pop(user_id, None)
            return

    finally:
        db.close()

    # 口座番号を保存して次のステップへ
    transfer_data['to_account_number'] = text
    transfer_data['step'] = 'amount'
    sessions[user_id]['transfer'] = transfer_data

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=f"振込先: {to_branch_code}-{text}\n\n次に、振込金額を入力してください。\n現在の残高: {transfer_data.get('from_balance')} JPY"
        )
    )


def _handle_amount_input(event, text, user_id, sessions, transfer_data):
    """金額入力処理"""
    # 数値チェック
    try:
        amount = Decimal(text)
        if amount <= 0:
            raise ValueError("金額は0より大きい値を入力してください。")

        # 残高チェック
        from_balance = Decimal(transfer_data.get('from_balance', '0'))
        if amount > from_balance:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex(
                    f"残高不足です。\n振込金額: {amount} JPY\n現在の残高: {from_balance} JPY",
                    'validation'
                )
            )
            # セッションをクリア
            sessions.pop(user_id, None)
            return

    except (InvalidOperation, ValueError) as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"有効な金額を入力してください。\n例: 1000\n\nエラー: {str(e)}")
        )
        return

    # 金額を保存して次のステップへ
    transfer_data['amount'] = str(amount)
    transfer_data['step'] = 'pin'
    sessions[user_id]['transfer'] = transfer_data

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=f"振込金額: {amount} JPY\n\n最後に、暗証番号（4桁）を入力してください。"
        )
    )


def _handle_pin_input(event, text, user_id, sessions, transfer_data):
    """暗証番号入力と振り込み実行"""
    # 4桁の数字チェック
    if not text.isdigit() or len(text) != 4:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="暗証番号は4桁の数字で入力してください。")
        )
        return

    # 認証と振り込み処理を実行
    _execute_transfer(event, text, user_id, sessions, transfer_data)


def _execute_transfer(event, pin_code, user_id, sessions, transfer_data):
    """振り込み実行処理

    Args:
        event: LINEイベントオブジェクト
        pin_code: 暗証番号
        user_id: ユーザーID
        sessions: セッション辞書
        transfer_data: 振り込みセッションデータ
    """
    from apps.banking.main_bank_system import SessionLocal, Account, Branch, Customer
    from sqlalchemy import select

    db = SessionLocal()
    try:
        # 振込元口座を取得
        from_branch = db.execute(
            select(Branch).filter_by(code=transfer_data.get('from_branch_code'))
        ).scalars().first()

        if not from_branch:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex("振込元口座の情報取得に失敗しました。", 'error')
            )
            sessions.pop(user_id, None)
            return

        from_account = db.execute(
            select(Account).filter_by(
                account_number=transfer_data.get('from_account_number'),
                branch_id=from_branch.branch_id
            )
        ).scalars().first()

        if not from_account:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex("振込元口座が見つかりません。", 'error')
            )
            sessions.pop(user_id, None)
            return

        # ステータスチェック: activeまたはfrozenのみ有効
        if from_account.status not in ('active', 'frozen'):
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex("この口座は利用できません（閉鎖済みまたは無効）。", 'error')
            )
            sessions.pop(user_id, None)
            return

        # 顧客情報を取得
        customer = db.execute(
            select(Customer).filter_by(customer_id=from_account.customer_id)
        ).scalars().first()

        if not customer:
            line_bot_api.reply_message(
                event.reply_token,
                get_transfer_error_flex("顧客情報の取得に失敗しました。", 'error')
            )
            sessions.pop(user_id, None)
            return

    finally:
        db.close()

    # 認証
    full_name = customer.full_name
    from_branch_code = transfer_data.get('from_branch_code')
    from_account_number = transfer_data.get('from_account_number')

    if not banking_api.authenticate_customer(
        full_name=full_name,
        pin_code=pin_code,
        branch_code=from_branch_code,
        account_number=from_account_number
    ):
        line_bot_api.reply_message(
            event.reply_token,
            get_transfer_error_flex("暗証番号が正しくありません。", 'auth')
        )
        sessions.pop(user_id, None)
        return

    # 振り込み処理を実行
    try:
        from apps.banking.bank_service import transfer_funds

        # 振込先口座情報を取得して名義を表示
        to_branch_code = transfer_data.get('to_branch_code')
        to_account_number = transfer_data.get('to_account_number')
        
        # 振込先の口座名義を取得
        to_account_info = None
        try:
            from apps.banking.main_bank_system import SessionLocal, Account, Branch
            from sqlalchemy import select
            
            db = SessionLocal()
            try:
                branch = db.execute(select(Branch).filter_by(code=to_branch_code)).scalars().first()
                if branch:
                    account = db.execute(
                        select(Account).filter_by(
                            account_number=to_account_number,
                            branch_id=branch.branch_id
                        )
                    ).scalars().first()
                    if account and account.customer:
                        to_account_info = account.customer.full_name
            finally:
                db.close()
        except Exception:
            pass
        
        # 摘要を作成：振込先の名義を含める
        description = f'振込: {to_account_info if to_account_info else to_account_number}'

        tx = transfer_funds(
            from_account_number=transfer_data.get('from_account_number'),
            to_account_number=transfer_data.get('to_account_number'),
            amount=transfer_data.get('amount'),
            currency='JPY',
            description=description
        )

        # 振込後の残高を取得
        updated_account = banking_api.get_accounts_by_user(user_id)
        new_balance = '0.00'
        for acc in updated_account:
            if (acc.get('account_number') == from_account_number and
                acc.get('branch_code') == from_branch_code):
                new_balance = acc.get('balance')
                break

        # 実行日時をフォーマット
        executed_at = now_jst().strftime('%Y/%m/%d %H:%M')

        # 金額をフォーマット
        try:
            amount_decimal = Decimal(transfer_data.get('amount'))
            amount_formatted = f"{amount_decimal:,.2f}"
        except Exception:
            amount_formatted = transfer_data.get('amount')

        # 成功メッセージを送信
        transfer_info = {
            'from_account_number': transfer_data.get('from_account_number'),
            'from_branch_code': transfer_data.get('from_branch_code'),
            'to_account_number': transfer_data.get('to_account_number'),
            'to_branch_code': transfer_data.get('to_branch_code'),
            'amount': amount_formatted,
            'currency': 'JPY',
            'executed_at': executed_at,
            'new_balance': new_balance
        }

        line_bot_api.reply_message(
            event.reply_token,
            get_transfer_success_flex(transfer_info)
        )

        # セッションをクリア
        sessions.pop(user_id, None)

    except Exception as e:
        error_message = str(e)
        if 'Insufficient funds' in error_message:
            error_message = "残高不足です。振り込みを完了できませんでした。"
        elif 'not found' in error_message.lower():
            error_message = "振込先口座が見つかりません。"
        elif 'not active' in error_message.lower():
            error_message = "指定された口座は利用できない状態です。"
        else:
            error_message = f"振り込み処理中にエラーが発生しました: {error_message}"

        line_bot_api.reply_message(
            event.reply_token,
            get_transfer_error_flex(error_message, 'error')
        )
        sessions.pop(user_id, None)


def cancel_transfer_session(event, user_id, sessions):
    """振り込みセッションをキャンセル

    Args:
        event: LINEイベントオブジェクト
        user_id: ユーザーID
        sessions: セッション辞書

    Returns:
        bool: キャンセルに成功した場合True
    """
    session = sessions.get(user_id)
    if session and 'transfer' in session:
        sessions.pop(user_id, None)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="振り込み手続きをキャンセルしました。")
        )
        return True
    return False
