"""
労働システムのコマンドハンドラー
"""
from linebot.models import TextSendMessage
from core.api import line_bot_api
from apps.work import work_service, work_flex
from apps.banking.api import banking_api


def handle_work_command(event, user_id):
    """?労働コマンド"""
    # 給与振込口座が登録されているか確認
    salary_info = work_service.get_salary_account_info(user_id)

    if not salary_info:
        # 未登録の場合、口座選択フローを開始
        bank_accounts = banking_api.get_accounts_by_user(user_id)

        if not bank_accounts or len(bank_accounts) == 0:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="銀行口座が見つかりません。先に「?口座開設」で銀行口座を作成してください。")
            )
            return

        # 口座が1つの場合は自動登録
        if len(bank_accounts) == 1:
            account_id = bank_accounts[0]['account_id']
            result = work_service.register_salary_account_by_id(user_id, account_id)

            if result['success']:
                # 登録成功後、すぐに労働を実行
                work_result = work_service.do_work(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"✅ 給与振込口座を登録しました\n\n{work_result['message']}\n\n💰 口座残高: ¥{work_result['balance_after']:,}")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"❌ {result['message']}")
                )
            return

        # 口座が複数の場合は選択画面を表示
        registration_flex = work_flex.get_salary_account_registration_flex(bank_accounts)
        line_bot_api.reply_message(event.reply_token, registration_flex)
        return

    # 登録済みの場合、労働を実行
    work_result = work_service.do_work(user_id)

    if work_result['success']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"💼 {work_result['message']}\n\n💰 口座残高: ¥{work_result['balance_after']:,}")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ {work_result['message']}")
        )


def handle_work_postback(event, data: dict, user_id: str):
    """労働システムのpostbackアクション処理"""
    action = data.get('action')

    if action == 'select_work_salary_account':
        # 口座選択（複数口座から選択した場合）
        account_id = int(data.get('account_id'))
        result = work_service.register_salary_account_by_id(user_id, account_id)

        if result['success']:
            # 登録成功後、すぐに労働を実行
            work_result = work_service.do_work(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ {result['message']}\n\n{work_result['message']}\n\n💰 口座残高: ¥{work_result['balance_after']:,}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ {result['message']}")
            )
        return True

    elif action == 'confirm_work_salary_account':
        # 口座登録確認（1つの口座のみの場合）
        account_id = int(data.get('account_id'))
        result = work_service.register_salary_account_by_id(user_id, account_id)

        if result['success']:
            # 登録成功後、すぐに労働を実行
            work_result = work_service.do_work(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ {result['message']}\n\n{work_result['message']}\n\n💰 口座残高: ¥{work_result['balance_after']:,}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ {result['message']}")
            )
        return True

    return False
