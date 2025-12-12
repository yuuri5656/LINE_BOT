"""
懲役システムの管理者コマンドハンドラー
"""
from datetime import datetime, date
from linebot.models import TextSendMessage, FlexSendMessage
from core.api import line_bot_api
from apps.prison import prison_service, prison_flex
from apps.banking.main_bank_system import SessionLocal, Account, Customer, Transaction
from sqlalchemy import select, and_
import config

# 管理者ユーザーID
ADMIN_USER_ID = "U87b0fbb89b407cda387dd29329c78259"


def is_admin(user_id: str) -> bool:
    """管理者チェック"""
    return user_id == ADMIN_USER_ID


def handle_admin_user_accounts(event, user_id: str, target_user_id: str):
    """
    ?ユーザー口座 [user_id] - 指定ユーザーの全口座を通帳形式で表示
    """
    if not is_admin(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です")
        )
        return
    
    db = SessionLocal()
    try:
        # ユーザーを確認
        customer = db.execute(
            select(Customer).where(Customer.user_id == target_user_id)
        ).scalars().first()
        
        if not customer:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ ユーザー {target_user_id} が見つかりません")
            )
            return
        
        # ユーザーの全口座を取得
        accounts = db.execute(
            select(Account).where(Account.user_id == target_user_id)
        ).scalars().all()
        
        if not accounts:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ ユーザー {target_user_id} に口座がありません")
            )
            return
        
        # 口座情報を通帳形式で表示
        from apps.help_flex import get_account_flex_bubble
        
        bubbles = [get_account_flex_bubble(acc) for acc in accounts if acc]
        
        if len(bubbles) == 1:
            flex_message = FlexSendMessage(
                alt_text=f"{target_user_id} の口座情報",
                contents=bubbles[0]
            )
        else:
            flex_message = FlexSendMessage(
                alt_text=f"{target_user_id} の口座情報一覧",
                contents={
                    "type": "carousel",
                    "contents": bubbles
                }
            )
        
        line_bot_api.reply_message(event.reply_token, flex_message)
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")
        )
    finally:
        db.close()


def handle_admin_account_number(event, user_id: str, account_number: str):
    """
    ?口座番号 [口座番号] - 口座番号から口座を検索して通帳形式で表示
    """
    if not is_admin(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です")
        )
        return
    
    db = SessionLocal()
    try:
        # 口座を検索
        account = db.execute(
            select(Account).where(Account.account_number == account_number)
        ).scalars().first()
        
        if not account:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ 口座番号 {account_number} が見つかりません")
            )
            return
        
        # 口座情報を通帳形式で表示
        from apps.help_flex import get_account_flex_bubble
        
        bubble = get_account_flex_bubble(account)
        
        flex_message = FlexSendMessage(
            alt_text=f"口座 {account_number} の情報",
            contents=bubble
        )
        
        line_bot_api.reply_message(event.reply_token, flex_message)
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")
        )
    finally:
        db.close()


def handle_admin_sentence(event, user_id: str, target_user_id: str, start_date_str: str, days: int, quota: int):
    """
    ?懲役 [user_id] [施行日] [日数] [ノルマ] - 懲役を設定
    """
    if not is_admin(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です")
        )
        return
    
    try:
        # 施行日をパース
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        
        # 懲役を設定
        result = prison_service.sentence_prisoner(
            target_user_id,
            start_date,
            days,
            quota
        )
        
        if result['success']:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=result['message'])
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ {result['message']}")
            )
    except ValueError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 施行日のフォーマットが正しくありません (YYYY-MM-DD を使用してください)")
        )
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")
        )


def handle_admin_freeze_account(event, user_id: str, account_number: str):
    """
    ?凍結 [口座番号] - 口座を凍結
    """
    if not is_admin(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です")
        )
        return
    
    db = SessionLocal()
    try:
        # 口座を検索
        account = db.execute(
            select(Account).where(Account.account_number == account_number)
        ).scalars().first()
        
        if not account:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ 口座番号 {account_number} が見つかりません")
            )
            return
        
        # 既に凍結されているか確認
        if account.status == 'frozen':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ 口座番号 {account_number} は既に凍結されています")
            )
            return
        
        # 口座を凍結
        account.status = 'frozen'
        db.add(account)
        db.commit()
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"✅ 口座番号 {account_number} を凍結しました")
        )
    except Exception as e:
        db.rollback()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")
        )
    finally:
        db.close()


def handle_admin_release(event, user_id: str, target_user_id: str):
    """
    ?釈放 [user_id] - ユーザーを釈放
    """
    if not is_admin(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ このコマンドは管理者のみ実行可能です")
        )
        return
    
    result = prison_service.release_prisoner(target_user_id)
    
    if result['success']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result['message'])
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ {result['message']}")
        )
