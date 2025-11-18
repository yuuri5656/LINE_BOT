from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from core.api import line_bot_api
from linebot.models import TextSendMessage
import random
import datetime
import time
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from apps.minigame.main_bank_system import (
    SessionLocal,
    Account,
    Branch,
    Customer,
    CustomerCredential,
    Transaction,
    TransactionEntry,
)
import config


# Argon2ハッシャーのインスタンス
ph = PasswordHasher()


def hash_pin(pin: str) -> tuple:
    """
    暗証番号をArgon2でハッシュ化する。
    Returns: (pin_hash, pin_salt) のタプル
    """
    # Argon2では内部でソルトを自動生成するため、明示的にソルトを生成する必要はない
    # ただし、DB設計でpin_saltカラムがあるため、便宜上ランダムな値を生成して保存
    pin_salt = secrets.token_hex(16)
    pin_hash = ph.hash(pin)
    return pin_hash, pin_salt


def verify_pin(pin: str, pin_hash: str) -> bool:
    """
    暗証番号をArgon2ハッシュと照合する。
    Returns: True if valid, False otherwise
    """
    try:
        ph.verify(pin_hash, pin)
        return True
    except VerifyMismatchError:
        return False


def generate_account_number(db: Session, branch: Branch, max_retries: int = 5) -> str:
    """
    7桁の口座番号を生成する。
    形式: [7桁のランダム数字]

    衝突が発生した場合はリトライする。
    Returns a numeric string of exactly 7 digits.
    """
    for attempt in range(max_retries):
        # 7桁のランダムな数字を生成
        acct = f"{random.randint(0, 9999999):07d}"

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
    - 顧客情報(customers)と認証情報(customer_credentials)の登録
    - 作成者(operator_id)が指定されていれば個別チャットへ口座情報を送信
    """
    display_name = account_info.get("display_name")
    db = SessionLocal()
    try:
        currency = "JPY"
        account_type_mapping = {
            "普通預金": "ordinary",
            "定期預金": "time",
            "当座預金": "current",
        }
        account_type_en = account_type_mapping.get(account_info.get('account_type'), 'ordinary')

        # 単一トランザクションで顧客・認証情報・支店・口座を作成
        with db.begin():
            user_id = account_info.get('user_id')
            full_name = account_info.get('full_name')
            birth_date_str = account_info.get('birth_date')
            pin_code = account_info.get('pin_code')

            # 既存顧客チェック
            customer = db.execute(select(Customer).filter_by(user_id=user_id)).scalars().first()
            if not customer:
                # 新規顧客を作成
                birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                customer = Customer(
                    user_id=user_id,
                    full_name=full_name,
                    date_of_birth=birth_date,
                )
                db.add(customer)
                db.flush()

                # 認証情報を作成
                pin_hash, pin_salt = hash_pin(pin_code)
                credential = CustomerCredential(
                    customer_id=customer.customer_id,
                    pin_hash=pin_hash,
                    pin_salt=pin_salt,
                )
                db.add(credential)
                db.flush()

            # 支店指定がある場合は code(branch_num)で取得または作成
            branch = None
            branch_num = account_info.get('branch_num')
            if branch_num:
                branch = db.execute(select(Branch).filter_by(code=str(branch_num))).scalars().first()
                if not branch:
                    branch = Branch(code=str(branch_num), name=f"Branch {branch_num}")
                    db.add(branch)
                    db.flush()

            else:
                # デフォルト支店(code='001'を優先)
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
                customer_id=customer.customer_id,
                user_id=user_id,
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

        # 返信はイベントに対して行うのはそのまま行う(呼び出し元でreplyされる想定)
        # push_messageは削除し、reply_account_creationで一元的に返信

        # Prepare a plain dict to return so callers do not need an active
        # SQLAlchemy Session to access attributes (avoids detached-instance errors).
        account_data = {
            'account_id': getattr(new_account, 'account_id', None),
            'customer_id': getattr(new_account, 'customer_id', None),
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
            # Normalize currency/status checks
            try:
                from_currency = str(getattr(from_acc, 'currency', '')).strip().upper()
            except Exception:
                from_currency = None
            try:
                to_currency = str(getattr(to_acc, 'currency', '')).strip().upper()
            except Exception:
                to_currency = None
            if from_currency != str(currency).strip().upper() or to_currency != str(currency).strip().upper():
                raise ValueError(f"Currency mismatch (from={repr(getattr(from_acc, 'currency', None))} to={repr(getattr(to_acc, 'currency', None))} expected={repr(currency)})")
            try:
                from_status = str(getattr(from_acc, 'status', '')).strip().lower()
            except Exception:
                from_status = None
            try:
                to_status = str(getattr(to_acc, 'status', '')).strip().lower()
            except Exception:
                to_status = None
            if from_status != 'active' or to_status != 'active':
                raise ValueError(f"One of accounts is not active (from_status={repr(getattr(from_acc, 'status', None))} to_status={repr(getattr(to_acc, 'status', None))})")
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


def get_account_info_by_user(user_id: str):
    """ユーザーIDから口座の主要情報を辞書で返す。口座が無ければ None を返す。"""
    db = SessionLocal()
    try:
        acc = db.execute(select(Account).filter_by(user_id=user_id)).scalars().first()
        if not acc:
            return None

        # branch はリレーション経由で取得可能（セッション内）
        branch_code = None
        branch_name = None
        try:
            if getattr(acc, 'branch', None):
                branch_code = getattr(acc.branch, 'code', None)
                branch_name = getattr(acc.branch, 'name', None)
        except Exception:
            branch_code = None
            branch_name = None

        balance = getattr(acc, 'balance', None)
        balance_str = format(balance, '.2f') if balance is not None else None

        info = {
            'account_id': getattr(acc, 'account_id', None),
            'account_number': getattr(acc, 'account_number', None),
            'balance': balance_str,
            'currency': getattr(acc, 'currency', None),
            'type': getattr(acc, 'type', None),
            'branch_code': branch_code,
            'branch_name': branch_name,
            'status': getattr(acc, 'status', None),
            'created_at': getattr(acc, 'created_at', None),
        }
        return info
    finally:
        db.close()


def get_account_transactions_by_user(user_id: str, limit: int = 20):
    """指定ユーザーの口座について、取引履歴（最近のものから）をリストで返す。
    各要素は dict を返す。口座が無ければ空リストを返す。
    """
    db = SessionLocal()
    try:
        acc = db.execute(select(Account).filter_by(user_id=user_id)).scalars().first()
        if not acc:
            return []

        # 口座関係のトランザクションを取得（from または to）
        txs = (
            db.execute(
                select(Transaction)
                .filter((Transaction.from_account_id == acc.account_id) | (Transaction.to_account_id == acc.account_id))
                .order_by(Transaction.executed_at.desc().nullslast(), Transaction.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        result = []
        for t in txs:
            try:
                direction = '出金' if t.from_account_id == acc.account_id else '入金'
                other_acc_num = None
                try:
                    if t.from_account_id == acc.account_id:
                        other_acc_num = getattr(t.to_account, 'account_number', None)
                    else:
                        other_acc_num = getattr(t.from_account, 'account_number', None)
                except Exception:
                    other_acc_num = None

                dt = t.executed_at if getattr(t, 'executed_at', None) else getattr(t, 'created_at', None)

                result.append({
                    'transaction_id': getattr(t, 'transaction_id', None),
                    'direction': direction,
                    'type': getattr(t, 'type', None),
                    'amount': format(getattr(t, 'amount', 0), '.2f'),
                    'currency': getattr(t, 'currency', None),
                    'other_account_number': other_acc_num,
                    'executed_at': dt,
                    'status': getattr(t, 'status', None),
                })
            except Exception:
                continue

        return result
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

        # 口座種別のマッピング
        account_type_display = {
            "普通預金": "普通",
            "定期預金": "定期",
            "当座預金": "当座"
        }
        acct_type = account_info.get('account_type') if account_info else None
        type_display = account_type_display.get(acct_type, '普通')
        
        # 発行年月の取得
        now = datetime.datetime.now()
        issue_date = f"{now.year % 100:02d}年/{now.month:02d}月"

        text = (
            f"口座の開設が完了しました。\n"
            f"氏名: {account_info.get('full_name') if account_info else '（不明）'}\n"
            f"表示名: {display_name if display_name else '（不明）'}\n"
            f"支店番号: {account_info.get('branch_num') if account_info else '（不明）'}\n"
            f"口座番号: {acct_num if acct_num else '（不明）'}\n"
            f"種別: {type_display}\n"
            f"発行年月: {issue_date}"
        )

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
    except Exception as e:
        print(f"[BankService] reply_account_creation failed: {e}")
        # Don't raise — caller can handle fallback reply


def withdraw_from_user(user_id: str, amount, currency: str = 'JPY'):
    """ユーザー口座から引き落とす。残高不足や口座未存在時は例外を投げる。
    transactionsテーブルとtransaction_entriesテーブルに記録される。
    """
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # Select by user_id and lock the row for update; check status in Python
            acc = db.execute(select(Account).filter_by(user_id=user_id).with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            # 正規化して比較(余分な空白や大文字小文字差を吸収)
            try:
                acc_currency = str(getattr(acc, 'currency', '')).strip().upper()
            except Exception:
                acc_currency = None
            if acc_currency != str(currency).strip().upper():
                raise ValueError(f"Currency mismatch (account={repr(getattr(acc, 'currency', None))} expected={repr(currency)})")
            try:
                acc_status = str(getattr(acc, 'status', '')).strip().lower()
            except Exception:
                acc_status = None
            if acc_status != 'active':
                raise ValueError(f"Account not active (status={repr(getattr(acc, 'status', None))})")
            if acc.balance < amt:
                raise ValueError("Insufficient funds")
            
            # 残高を更新
            acc.balance = acc.balance - amt
            
            # トランザクションレコード作成(出金)
            tx = Transaction(
                from_account_id=acc.account_id,
                to_account_id=None,
                amount=amt,
                currency=currency,
                type='withdrawal',
                status='completed',
                executed_at=datetime.datetime.utcnow(),
            )
            db.add(tx)
            db.flush()
            
            # 二重仕訳エントリ(出金は debit)
            debit_entry = TransactionEntry(
                transaction_id=tx.transaction_id,
                account_id=acc.account_id,
                entry_type='debit',
                amount=amt,
            )
            db.add(debit_entry)
            
        return True
    except Exception as e:
        # 詳細ログを出して原因を把握しやすくする
        try:
            acc = locals().get('acc', None)
            acc_info = None
            if acc is not None:
                try:
                    acc_info = f"account_id={getattr(acc, 'account_id', None)} balance={getattr(acc, 'balance', None)} status={getattr(acc, 'status', None)} currency={getattr(acc, 'currency', None)}"
                except Exception:
                    acc_info = "(failed to read account info)"
            else:
                acc_info = "(no account found)"
        except Exception:
            acc_info = "(error while preparing account info)"
        try:
            print(f"[BankService] withdraw_from_user failed user={user_id} amount={amt} currency={currency} error={e} acc_info={acc_info}")
        except Exception:
            pass
        db.rollback()
        raise
    finally:
        db.close()


def deposit_to_user(user_id: str, amount, currency: str = 'JPY'):
    """ユーザー口座へ入金する。口座が存在しない場合は例外を投げる。
    transactionsテーブルとtransaction_entriesテーブルに記録される。
    """
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # Select by user_id and lock the row for update; check status in Python
            acc = db.execute(select(Account).filter_by(user_id=user_id).with_for_update()).scalars().first()
            if not acc:
                raise ValueError("Account not found")
            # Normalize for robustness
            try:
                acc_currency = str(getattr(acc, 'currency', '')).strip().upper()
            except Exception:
                acc_currency = None
            if acc_currency != str(currency).strip().upper():
                raise ValueError(f"Currency mismatch (account={repr(getattr(acc, 'currency', None))} expected={repr(currency)})")
            try:
                acc_status = str(getattr(acc, 'status', '')).strip().lower()
            except Exception:
                acc_status = None
            if acc_status != 'active':
                raise ValueError(f"Account not active (status={repr(getattr(acc, 'status', None))})")
            
            # 残高を更新
            acc.balance = acc.balance + amt
            
            # トランザクションレコード作成(入金)
            tx = Transaction(
                from_account_id=None,
                to_account_id=acc.account_id,
                amount=amt,
                currency=currency,
                type='deposit',
                status='completed',
                executed_at=datetime.datetime.utcnow(),
            )
            db.add(tx)
            db.flush()
            
            # 二重仕訳エントリ(入金は credit)
            credit_entry = TransactionEntry(
                transaction_id=tx.transaction_id,
                account_id=acc.account_id,
                entry_type='credit',
                amount=amt,
            )
            db.add(credit_entry)
            
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def authenticate_customer(user_id: str, full_name: str, date_of_birth: str, pin_code: str) -> bool:
    """
    ミニゲーム参加時の顧客認証API。
    user_id、フルネーム、生年月日、暗証番号を照合する。
    
    Args:
        user_id: LINE user ID
        full_name: 登録時のフルネーム
        date_of_birth: 生年月日(YYYY-MM-DD形式の文字列)
        pin_code: 4桁の暗証番号
    
    Returns:
        True if authenticated, False otherwise
    """
    db = SessionLocal()
    try:
        # 顧客情報を取得
        customer = db.execute(select(Customer).filter_by(user_id=user_id)).scalars().first()
        if not customer:
            return False
        
        # フルネームの照合
        if customer.full_name != full_name:
            return False
        
        # 生年月日の照合
        try:
            birth_date = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            if customer.date_of_birth != birth_date:
                return False
        except ValueError:
            return False
        
        # 認証情報を取得
        credential = db.execute(
            select(CustomerCredential).filter_by(customer_id=customer.customer_id)
        ).scalars().first()
        if not credential:
            return False
        
        # 暗証番号の照合(Argon2)
        if not verify_pin(pin_code, credential.pin_hash):
            return False
        
        return True
    except Exception as e:
        print(f"[BankService] authenticate_customer error: {e}")
        return False
    finally:
        db.close()
