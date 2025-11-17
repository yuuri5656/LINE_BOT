"""
口座開設処理モジュール
bank_receptionから顧客情報を受け取り、アカウント作成を実行する
"""
from core.api import line_bot_api
from linebot.models import TextSendMessage
from apps.minigame.bank_service import create_account_optimized


def create_account(event, account_info, sessions, user_id):
    """シンプルなラッパー: 最適化済みの口座作成処理を呼び出す"""
    try:
        # operator_id を sessions や account_info から取り出せる場合は渡す
        operator_id = account_info.get('operator_id') or sessions.get('operator_id') if sessions else None
        new_account = create_account_optimized(event, account_info, sessions, operator_id=operator_id)

        acct_num = None
        try:
            # bank_service now returns a plain dict for safety
            acct_num = new_account.get('account_number') if isinstance(new_account, dict) else getattr(new_account, 'account_number', None)
        except Exception:
            acct_num = None

        messages = [
            TextSendMessage(
                text=(
                    f"{account_info.get('display_name')} 様、ご登録ありがとうございます。\n\n"
                    f"口座を開設いたしました。\n口座番号: {acct_num if acct_num else '（不明）'}"
                )
            ),
        ]
        line_bot_api.reply_message(event.reply_token, messages)

    except Exception as e:
        print(f"[Account Creation Wrapper Error] {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ございません。口座開設処理中にエラーが発生しました。後ほどお試しください。")
        )
