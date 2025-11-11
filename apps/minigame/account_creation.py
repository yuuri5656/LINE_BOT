"""
口座開設処理モジュール
bank_receptionから顧客情報を受け取り、アカウント作成を実行する
"""
from core.api import line_bot_api
from linebot.models import TextSendMessage
import config
import psycopg2
from sqlalchemy.orm import sessionmaker
from apps.minigame.main_bank_system import engine, Account
import uuid


def create_account(event, account_info, sessions, user_id):
    """
    顧客情報を受け取り、データベースに口座を作成する

    Args:
        event: LINE Botイベント
        account_info: 顧客情報を含む辞書
            - user_id: ユーザーID (LINE ID)
            - full_name: フルネーム
            - birth_date: 生年月日 (YYYY-MM-DD形式)
            - account_type: 口座種別 (普通預金 / 当座預金 / 定期預金)
            - pin_code: 暗証番号
            - display_name: 表示名
        sessions: セッション管理辞書
        user_id: ユーザーID
    """

    display_name = account_info.get("display_name")

    try:
        # SQLAlchemyを使用してセッションを作成
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()

        # 顧客情報をログ出力（デバッグ用）
        print(f"[Account Creation] User: {user_id}, Name: {account_info.get('full_name')}")
        print(f"  Birth Date: {account_info.get('birth_date')}")
        print(f"  Account Type: {account_info.get('account_type')}")
        print(f"  PIN: {account_info.get('pin_code')}")

        # 口座作成のための準備
        # 実際のDB操作はここに実装される予定

        # 一意の口座番号を生成
        account_number = generate_account_number()

        # 通貨タイプを設定（現在は日本円を仮定）
        currency = "JPY"

        # 口座種別から口座タイプをマッピング
        account_type_mapping = {
            "普通預金": "savings",
            "当座預金": "checking",
            "定期預金": "time_deposit"
        }

        # セッション情報を保存（後のDB操作のため）
        print(f"[Account Creation] Account Number: {account_number}")
        print(f"[Account Creation] Currency: {currency}")

        # ここでDB操作を実行する前に、クライアントに確認メッセージを送信
        messages = []
        messages.append(TextSendMessage(
            text=f"{display_name} 様、ご登録ありがとうございます。\n\n"
                f"以下の内容で口座を開設いたします：\n"
                f"- お名前: {account_info.get('full_name')} 様\n"
                f"- 生年月日: {account_info.get('birth_date')}\n"
                f"- 口座種別: {account_info.get('account_type')}"
        ))
        messages.append(TextSendMessage(
            text="手続きが完了いたしました。\n\n"
                "口座情報等につきましては、手続き完了次第このLINEにてご連絡いたします。"
        ))

        line_bot_api.reply_message(event.reply_token, messages)

        # TODO: 実際のDB操作をここに追加
        # 以下は準備段階のみ
        print("[Account Creation] Ready for DB insertion (actual insertion not yet implemented)")

        db_session.close()

    except Exception as e:
        print(f"[Account Creation Error] {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ございません。口座開設処理中にエラーが発生しました。\nお手数ですが、後ほどお試しください。")
        )


def generate_account_number():
    """
    一意の口座番号を生成する

    Returns:
        str: 生成された口座番号
    """
    # UUIDの一部を使用して一意の口座番号を生成
    # 実際の銀行システムではより適切なロジックを使用すること
    unique_id = str(uuid.uuid4()).replace("-", "")[:16]
    return f"ACCT-{unique_id}"
