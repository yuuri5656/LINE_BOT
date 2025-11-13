"""
口座開設処理モジュール
bank_receptionから顧客情報を受け取り、アカウント作成を実行する
"""
from core.api import line_bot_api
from linebot.models import TextSendMessage
import config
import psycopg2
from sqlalchemy.orm import sessionmaker
from apps.minigame.main_bank_system import engine, Account, Branch
import uuid
from decimal import Decimal


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

    # SQLAlchemyを使用してセッションを作成
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    try:
        # 顧客情報をログ出力（デバッグ用）
        print(f"[Account Creation] User: {user_id}, Name: {account_info.get('full_name')}")
        print(f"  Birth Date: {account_info.get('birth_date')}")
        print(f"  Account Type: {account_info.get('account_type')}")
        print(f"  PIN: {account_info.get('pin_code')}")

        # 一意の口座番号を生成
        account_number = generate_account_number()

        # 通貨タイプを設定（現在は日本円を仮定）
        currency = "JPY"

        # 日本語の口座種別を DB の ENUM 用に英語にマッピング
        account_type_mapping = {
            "普通預金": "savings",
            "当座預金": "checking",
            "定期預金": "time_deposit"
        }

        account_type_en = account_type_mapping.get(account_info.get('account_type'))
        if account_type_en is None:
            # 予期しない値が来た場合はデフォルトを 'savings' にする
            account_type_en = 'savings'

        # DBへ送る想定のペイロード
        db_payload = {
            'user_id': user_id,
            'account_number': account_number,
            'account_type': account_type_en,
            'currency': currency,
            'balance': Decimal('0')
        }

        # ログ出力
        print(f"[Account Creation] Account Number: {account_number}")
        print(f"[Account Creation] Currency: {currency}")
        print(f"[Account Creation] Account Type (EN): {account_type_en}")

        # デフォルトブランチを取得または作成（システムの初期化時に必要に応じて設定）
        # ここでは、branch_id=1 を仮定（実運用では設定可能に）
        default_branch_id = 1
        
        # Account オブジェクトを生成
        new_account = Account(
            user_id=db_payload['user_id'],
            account_number=db_payload['account_number'],
            balance=db_payload['balance'],
            currency=db_payload['currency'],
            type=db_payload['account_type'],
            branch_id=default_branch_id,
            status='active'  # デフォルトはアクティブ
        )

        # トランザクション内で DB に挿入
        db_session.add(new_account)
        db_session.commit()

        print(f"[Account Creation] Successfully created account: {account_number}")
        print(f"[Account Creation] DB Payload: {db_payload}")

        # ここでDB操作を実行してから、クライアントに確認メッセージを送信
        messages = []
        messages.append(TextSendMessage(
            text=f"{display_name} 様、ご登録ありがとうございます。\n\n"
                f"以下の内容で口座を開設いたしました：\n"
                f"- お名前: {account_info.get('full_name')} 様\n"
                f"- 生年月日: {account_info.get('birth_date')}\n"
                f"- 口座種別: {account_info.get('account_type')}\n"
                f"- 口座番号: {account_number}"
        ))
        messages.append(TextSendMessage(
            text="手続きが完了いたしました。\n\n"
                "口座情報等につきましては、手続き完了次第このLINEにてご連絡いたします。"
        ))

        line_bot_api.reply_message(event.reply_token, messages)

    except Exception as e:
        # エラーが発生した場合はロールバック
        db_session.rollback()
        print(f"[Account Creation Error] {str(e)}")
        import traceback
        traceback.print_exc()
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ございません。口座開設処理中にエラーが発生しました。\nお手数ですが、後ほどお試しください。")
        )
    finally:
        db_session.close()


def generate_account_number():
    """
    一意の口座番号を生成する

    Returns:
        str: 生成された口座番号
    """
    # UUIDの一部を使用して一意の口座番号を生成
    # 実際の銀行システムではより適切なロジックを使用すること
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{unique_id}"
