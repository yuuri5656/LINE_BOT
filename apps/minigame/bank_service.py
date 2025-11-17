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

        # Detach instance from session so callers can safely access attributes
        try:
            db.expunge(new_account)
        except Exception:
            # expunge may fail for some session implementations; ignore safely
            pass
        return new_account

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
        acc = db.execute(select(Account).filter_by(user_id=user_id, status='active')).scalars().first()
        return acc
    finally:
        db.close()


def withdraw_from_user(user_id: str, amount, currency: str = 'JPY'):
    """ユーザー口座から引き落とす。残高不足や口座未存在時は例外を投げる。"""
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            acc = db.execute(select(Account).filter_by(user_id=user_id, status='active').with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            if acc.currency != currency:
                raise ValueError("Currency mismatch")
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
            acc = db.execute(select(Account).filter_by(user_id=user_id, status='active').with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            if acc.currency != currency:
                raise ValueError("Currency mismatch")
            acc.balance = acc.balance + amt
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
