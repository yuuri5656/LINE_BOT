from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from core.api import line_bot_api
from linebot.models import TextSendMessage
import random
import datetime
import time

from apps.minigame.main_bank_system import (
    SessionLocal,
    Account,
    Branch,
    Transaction,
    TransactionEntry,
)
import config


def generate_account_number(db: Session, branch: Branch, max_retries: int = 5) -> str:
    """
    支店番号を織り込んだ整数列の口座番号を生成する。
    形式: [branch_id:3桁][YYYYMMDDHHMMSS][rand:3]

    衝突が発生した場合はリトライする。
    Returns a numeric string.
    """
    for attempt in range(max_retries):
        ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rand = f"{random.randint(0,999):03d}"
        # 支店コードが設定されていればそれを優先して使用（数値文字列で左ゼロ埋め）、
        # そうでなければ branch_id を 3 桁で使用する
        branch_part = None
        try:
            code = getattr(branch, 'code', None)
            if code and isinstance(code, str) and code.isdigit():
                branch_part = code.zfill(3)
        except Exception:
            branch_part = None

        if not branch_part:
            branch_part = f"{getattr(branch, 'branch_id', 0):03d}"

        acct = f"{branch_part}{ts}{rand}"

        # 衝突チェック
        existing = db.execute(select(Account).filter_by(account_number=acct)).scalars().first()
        if not existing:
            return acct
        time.sleep(0.05)

    raise RuntimeError("Failed to generate unique account number after retries")


def create_account_optimized(event, account_info: dict, sessions: dict, operator_id: str = None):
    """
    より堅牢な口座作成処理。
    - トランザクション管理
    - 支店を考慮した口座番号生成
    - 作成者（operator_id）が指定されていれば個別チャットへ口座情報を送信
    """
    display_name = account_info.get("display_name")
    db = SessionLocal()
    try:
        currency = "JPY"
        account_type_mapping = {
            "普通預金": "ordinary",
            "定期預金": "time",
        }
        account_type_en = account_type_mapping.get(account_info.get('account_type'), 'ordinary')

        # 単一トランザクションで branch の取得/作成と口座生成・挿入を行う
        with db.begin():
            # 支店指定がある場合は code（branch_num）で取得または作成
            branch = None
            branch_num = account_info.get('branch_num')
            if branch_num:
                branch = db.execute(select(Branch).filter_by(code=str(branch_num))).scalars().first()
                if not branch:
                    branch = Branch(code=str(branch_num), name=f"Branch {branch_num}")
                    db.add(branch)
                    db.flush()

            else:
                # デフォルト支店（code='001' を優先）
                branch = db.execute(select(Branch).filter_by(code='001')).scalars().first()
                if not branch:
                    branch = db.execute(select(Branch).filter_by(branch_id=1)).scalars().first()
                if not branch:
                    branch = Branch(code="001", name="Main Branch")
                    db.add(branch)
                    db.flush()

            # 口座番号生成
            account_number = generate_account_number(db, branch)

            new_account = Account(
                user_id=account_info.get('user_id'),
                account_number=account_number,
                balance=Decimal('0'),
                currency=currency,
                type=account_type_en,
                branch_id=branch.branch_id,
            )

            db.add(new_account)
            # Ensure PK and attributes are populated before returning a detached instance
            db.flush()
            db.refresh(new_account)

        # 返信はイベントに対して行うのはそのまま行う（呼び出し元でreplyされる想定）
        # 口座開設者（account_info['user_id']）へ個別チャットで通知を送信
        try:
            opener_user_id = account_info.get('user_id')
            if opener_user_id:
                msg = TextSendMessage(
                    text=(
                        f"口座開設が完了しました。\nユーザー: {display_name}\n"
                        f"口座番号: {account_number}\n通貨: {currency}\n種類: {account_info.get('account_type')}"
                    )
                )
                try:
                    line_bot_api.push_message(opener_user_id, msg)
                except Exception as e:
                    print(f"[BankService] Failed to push message to opener {opener_user_id}: {e}")
        except Exception as e:
            print(f"[BankService] notification error: {e}")

        # Prepare a plain dict to return so callers do not need an active
        # SQLAlchemy Session to access attributes (avoids detached-instance errors).
        account_data = {
            'account_id': getattr(new_account, 'account_id', None),
            'user_id': getattr(new_account, 'user_id', None),
            'account_number': getattr(new_account, 'account_number', None),
            'balance': str(getattr(new_account, 'balance', None)),
            'currency': getattr(new_account, 'currency', None),
            'type': getattr(new_account, 'type', None),
            'branch_id': getattr(new_account, 'branch_id', None),
            'status': getattr(new_account, 'status', None),
        }

        # Detach instance from session to be safe (callers will use the dict)
        try:
            db.expunge(new_account)
        except Exception:
            pass
        return account_data

    except Exception as e:
        db.rollback()
        print(f"[BankService] create_account_optimized error: {e}")
        raise
    finally:
        db.close()


def transfer_funds(from_account_number: str, to_account_number: str, amount, currency: str = 'JPY'):
    """
    送金処理: 二重仕訳 + 残高更新 を単一の DB トランザクションで行う。
    Returns the Transaction object.
    """
    db = SessionLocal()
    amount = Decimal(amount)
    try:
        with db.begin():
            # 送金元・送金先をロックして取得
            from_acc = db.execute(select(Account).filter_by(account_number=from_account_number).with_for_update()).scalars().first()
            to_acc = db.execute(select(Account).filter_by(account_number=to_account_number).with_for_update()).scalars().first()

            if not from_acc:
                raise ValueError("From account not found")
            if not to_acc:
                raise ValueError("To account not found")
            if from_acc.currency != currency or to_acc.currency != currency:
                raise ValueError("Currency mismatch")
            if from_acc.status != 'active' or to_acc.status != 'active':
                raise ValueError("One of accounts is not active")
            if from_acc.balance < amount:
                raise ValueError("Insufficient funds")

            # トランザクションレコード作成
            tx = Transaction(
                from_account_id=from_acc.account_id,
                to_account_id=to_acc.account_id,
                amount=amount,
                currency=currency,
                type='transfer',
                status='executed',
                executed_at=datetime.datetime.utcnow(),
            )
            db.add(tx)
            db.flush()  # tx.transaction_id を得るため

            # 二重仕訳エントリ
            debit_entry = TransactionEntry(
                transaction_id=tx.transaction_id,
                account_id=from_acc.account_id,
                entry_type='debit',
                amount=amount,
            )
            credit_entry = TransactionEntry(
                transaction_id=tx.transaction_id,
                account_id=to_acc.account_id,
                entry_type='credit',
                amount=amount,
            )
            db.add_all([debit_entry, credit_entry])

            # 残高更新
            from_acc.balance = from_acc.balance - amount
            to_acc.balance = to_acc.balance + amount

        # commit は with db.begin() で行われる
        return tx

    except Exception as e:
        db.rollback()
        print(f"[BankService] transfer_funds failed: {e}")
        raise
    finally:
        db.close()


def get_active_account_by_user(user_id: str):
    """ユーザーIDからアクティブな口座を取得するヘルパー。見つからなければ None を返す。"""
    db = SessionLocal()
    try:
        # Avoid passing the literal enum value into the SQLAlchemy filter because
        # the PG ENUM reflection may not provide Python-side enum choices in all
        # runtime environments. Instead select by user_id and check the status
        # value in Python.
        acc = db.execute(select(Account).filter_by(user_id=user_id)).scalars().first()
        if not acc:
            return None
        try:
            return acc if getattr(acc, 'status', None) == 'active' else None
        except Exception:
            return None
    finally:
        db.close()


def reply_account_creation(event, account_info: dict, account_data: dict):
    """
    `create_account_optimized` の呼び出し元に対して、
    口座開設完了の文面を統一して返信するヘルパー。
    - `event` : LINE のイベントオブジェクト（reply_token を含む）
    - `account_info` : 送信者や表示名などの元情報
    - `account_data` : `create_account_optimized` が返す dict
    """
    try:
        display_name = account_info.get('display_name') if account_info else None
        acct_num = None
        try:
            acct_num = account_data.get('account_number') if isinstance(account_data, dict) else getattr(account_data, 'account_number', None)
        except Exception:
            acct_num = None

        currency = account_data.get('currency') if isinstance(account_data, dict) else getattr(account_data, 'currency', 'JPY')
        acct_type = account_info.get('account_type') if account_info else None

        text = (
            f"口座開設が完了しました。\n"
            f"ユーザー: {display_name if display_name else '（不明）'}\n"
            f"口座番号: {acct_num if acct_num else '（不明）'}\n"
            f"通貨: {currency}\n"
            f"種類: {acct_type if acct_type else '（不明）'}"
        )

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
    except Exception as e:
        print(f"[BankService] reply_account_creation failed: {e}")
        # Don't raise — caller can handle fallback reply


def withdraw_from_user(user_id: str, amount, currency: str = 'JPY'):
    """ユーザー口座から引き落とす。残高不足や口座未存在時は例外を投げる。"""
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # Select by user_id and lock the row for update; check status in Python
            acc = db.execute(select(Account).filter_by(user_id=user_id).with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            if acc.currency != currency:
                raise ValueError("Currency mismatch")
            if getattr(acc, 'status', None) != 'active':
                raise ValueError("Account not active")
            if acc.balance < amt:
                raise ValueError("Insufficient funds")
            acc.balance = acc.balance - amt
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def deposit_to_user(user_id: str, amount, currency: str = 'JPY'):
    """ユーザー口座へ入金する。口座が存在しない場合は例外を投げる。"""
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # Select by user_id and lock the row for update; check status in Python
            acc = db.execute(select(Account).filter_by(user_id=user_id).with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            if acc.currency != currency:
                raise ValueError("Currency mismatch")
            if getattr(acc, 'status', None) != 'active':
                raise ValueError("Account not active")
            acc.balance = acc.balance + amt
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
