from decimal import Decimal

# ミニゲーム手数料受取口座（運営口座）
MINIGAME_FEE_ACCOUNT = {
    "full_name": "ﾐﾆｹﾞｰﾑ ｳﾝｴｲ",
    "display_name": "🅺🅸🅼🆄🆁🅰",
    "branch_num": "006",
    "account_number": "6291119",
    "account_type": "当座",
    "issue_date": "25年/11月"
}
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
    MinigameAccount,
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

        # 必須項目バリデーション
        required_fields = ['user_id', 'full_name', 'birth_date', 'pin_code']
        missing = [f for f in required_fields if not account_info.get(f)]
        if missing:
            raise ValueError(f"口座作成に必要な情報が不足しています: {', '.join(missing)}")

        # 単一トランザクションで顧客・認証情報・支店・口座を作成
        with db.begin():
            user_id = account_info.get('user_id')
            full_name = account_info.get('full_name')
            birth_date_str = account_info.get('birth_date')
            pin_code = account_info.get('pin_code')


            # 既存顧客チェック（user_id, full_name, date_of_birthの組み合わせで判定）
            birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            customer = db.execute(
                select(Customer).filter_by(user_id=user_id, full_name=full_name, date_of_birth=birth_date)
            ).scalars().first()
            if not customer:
                # 新規顧客を作成
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


    def get_accounts_by_user(user_id: str):
        """ユーザーIDに紐づく全口座情報をリストで返す。"""
        db = SessionLocal()
        try:
            accounts = db.execute(select(Account).filter_by(user_id=user_id)).scalars().all()
            result = []
            for acc in accounts:
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
                result.append(info)
            return result
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


def withdraw_by_account_number(account_number: str, branch_code: str, amount, currency: str = 'JPY'):
    """
    口座番号と支店コードから引き落とす。残高不足や口座未存在時は例外を投げる。
    transactionsテーブルとtransaction_entriesテーブルに記録される。
    
    Args:
        account_number: 口座番号
        branch_code: 支店コード
        amount: 引き落とし額
        currency: 通貨コード(デフォルトはJPY)
    
    Returns:
        True if successful
    
    Raises:
        ValueError: 口座が見つからない、残高不足、口座が非アクティブなど
    """
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # 支店情報を取得
            branch = db.execute(select(Branch).filter_by(code=str(branch_code))).scalars().first()
            if not branch:
                raise ValueError(f"Branch not found: {branch_code}")
            
            # 口座番号と支店IDで口座を取得してロック
            acc = db.execute(
                select(Account)
                .filter_by(account_number=account_number, branch_id=branch.branch_id)
                .with_for_update()
            ).scalars().first()
            
            if not acc:
                raise ValueError(f"Account not found: {account_number} at branch {branch_code}")
            
            # 通貨チェック
            try:
                acc_currency = str(getattr(acc, 'currency', '')).strip().upper()
            except Exception:
                acc_currency = None
            if acc_currency != str(currency).strip().upper():
                raise ValueError(f"Currency mismatch (account={repr(getattr(acc, 'currency', None))} expected={repr(currency)})")
            
            # 口座ステータスチェック
            try:
                acc_status = str(getattr(acc, 'status', '')).strip().lower()
            except Exception:
                acc_status = None
            if acc_status != 'active':
                raise ValueError(f"Account not active (status={repr(getattr(acc, 'status', None))})")
            
            # 残高チェック
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
        db.rollback()
        print(f"[BankService] withdraw_by_account_number failed account={account_number} branch={branch_code} amount={amt} currency={currency} error={e}")
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


def deposit_by_account_number(account_number: str, branch_code: str, amount, currency: str = 'JPY'):
    """
    口座番号と支店コードで入金する。口座が存在しない場合は例外を投げる。
    transactionsテーブルとtransaction_entriesテーブルに記録される。
    
    Args:
        account_number: 口座番号
        branch_code: 支店コード
        amount: 入金額
        currency: 通貨コード(デフォルトはJPY)
    
    Returns:
        True if successful
    
    Raises:
        ValueError: 口座が見つからない、口座が非アクティブなど
    """
    db = SessionLocal()
    amt = Decimal(amount)
    try:
        with db.begin():
            # 支店情報を取得
            branch = db.execute(select(Branch).filter_by(code=str(branch_code))).scalars().first()
            if not branch:
                raise ValueError(f"Branch not found: {branch_code}")
            
            # 口座番号と支店IDで口座を取得してロック
            acc = db.execute(
                select(Account)
                .filter_by(account_number=account_number, branch_id=branch.branch_id)
                .with_for_update()
            ).scalars().first()
            
            if not acc:
                raise ValueError(f"Account not found: {account_number} at branch {branch_code}")
            
            # 通貨チェック
            try:
                acc_currency = str(getattr(acc, 'currency', '')).strip().upper()
            except Exception:
                acc_currency = None
            if acc_currency != str(currency).strip().upper():
                raise ValueError(f"Currency mismatch (account={repr(getattr(acc, 'currency', None))} expected={repr(currency)})")
            
            # 口座ステータスチェック
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
    except Exception as e:
        db.rollback()
        print(f"[BankService] deposit_by_account_number failed account={account_number} branch={branch_code} amount={amt} currency={currency} error={e}")
        raise
    finally:
        db.close()


def authenticate_customer(full_name: str, pin_code: str, branch_code: str = None, account_number: str = None) -> bool:
    """
    ミニゲーム参加時の顧客認証API。
    フルネーム、暗証番号を照合する。
    オプションで支店番号と口座番号も照合可能。

    Args:
        branch_code: 支店番号
        account_number: 口座番号
        full_name: 登録時のフルネーム(半角カタカナ)
        pin_code: 4桁の暗証番号

    Returns:
        True if authenticated, False otherwise
    """
    db = SessionLocal()
    try:
        # 支店番号と口座番号を照合
        # 支店情報を取得
        branch = db.execute(select(Branch).filter_by(code=str(branch_code))).scalars().first()
        if not branch:
            return False

        # branch_codeをbranchesテーブルを参照し、branch_idに変換
        branch_id = branch.branch_id if branch else None

        # 口座情報を取得
        account = db.execute(
            select(Account).filter_by(
                account_number=account_number,
                branch_id=branch_id
            )
        ).scalars().first()
        if not account:
            return False

        # 口座がアクティブか確認
        try:
            acc_status = str(getattr(account, 'status', '')).strip().lower()
        except Exception:
            acc_status = None
        if acc_status != 'active':
            return False

        # accountsテーブルから、account_numberとbranch_idが合致するレコードのcustomer_idを取得
        customer_id = account.customer_id if account else None

        # customersテーブルから、customer_idが合致するレコードを取得
        customer = db.execute(
            select(Customer).filter_by(customer_id=customer_id)
        ).scalars().first()
        if not customer:
            return False

        # フルネームの照合
        if customer.full_name != full_name:
            return False

        # 認証情報を取得
        credential = db.execute(
            select(CustomerCredential).filter_by(customer_id=customer_id)
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


def register_minigame_account(user_id: str, full_name: str, branch_code: str, account_number: str, pin_code: str) -> dict:
    """
    ユーザーの既存口座をミニゲーム用口座として登録する。
    既存の口座をミニゲーム専用として登録する。
    支店番号、口座番号、氏名、暗証番号で本人確認を行う。

    Args:
        user_id: LINE user ID
        full_name: フルネーム（口座開設時に登録したもの、半角カタカナ）
        branch_code: 支店番号（登録したい既存口座の支店番号）
        account_number: 口座番号（登録したい既存口座の口座番号）
        pin_code: 暗証番号（口座開設時に設定したもの）

    Returns:
        成功時: {'success': True, 'minigame_account_id': int, 'message': str, 'updated': bool}
        失敗時: {'success': False, 'error': str}
    """
    db = SessionLocal()
    try:
        # まず認証を行う
        if not authenticate_customer(full_name, pin_code, branch_code, account_number):
            return {'success': False, 'error': '認証に失敗しました。入力情報を確認してください。'}

        with db.begin():
            # 支店情報を取得
            branch = db.execute(select(Branch).filter_by(code=str(branch_code))).scalars().first()
            if not branch:
                return {'success': False, 'error': '指定された支店番号が見つかりません。'}

            # 口座の存在確認
            account = db.execute(
                select(Account).filter_by(account_number=account_number, branch_id=branch.branch_id)
            ).scalars().first()

            if not account:
                return {'success': False, 'error': '指定された口座番号が見つかりません。'}

            # 口座の所有者確認
            if account.user_id != user_id:
                return {'success': False, 'error': 'この口座はあなたの口座ではありません。'}

            # 口座がアクティブか確認
            try:
                acc_status = str(getattr(account, 'status', '')).strip().lower()
            except Exception:
                acc_status = None
            if acc_status != 'active':
                return {'success': False, 'error': 'この口座は現在使用できません（凍結または閉鎖されています）。'}

            # 既にミニゲーム口座として登録されているか確認（同じuser_id）
            existing = db.execute(
                select(MinigameAccount).filter_by(user_id=user_id)
            ).scalars().first()

            if existing:
                # 既存のミニゲーム口座を更新
                existing.account_id = account.account_id
                existing.is_active = True
                existing.registered_at = datetime.datetime.now()
                db.flush()

                return {
                    'success': True,
                    'minigame_account_id': existing.minigame_account_id,
                    'message': 'ミニゲーム用口座を更新しました。',
                    'updated': True
                }

            # この口座が他のユーザーのミニゲーム口座として登録されていないか確認
            account_used = db.execute(
                select(MinigameAccount).filter_by(account_id=account.account_id)
            ).scalars().first()

            if account_used:
                return {'success': False, 'error': 'この口座は既に他のユーザーのミニゲーム口座として登録されています。'}

            # 新規登録
            minigame_acc = MinigameAccount(
                user_id=user_id,
                account_id=account.account_id,
                registered_at=datetime.datetime.now(),
                is_active=True
            )
            db.add(minigame_acc)
            db.flush()

            return {
                'success': True,
                'minigame_account_id': minigame_acc.minigame_account_id,
                'message': 'ミニゲーム用口座を登録しました。',
                'updated': False
            }

    except Exception as e:
        db.rollback()
        print(f"[BankService] register_minigame_account error: {e}")
        return {'success': False, 'error': f'登録中にエラーが発生しました: {str(e)}'}
    finally:
        db.close()


def get_minigame_account(user_id: str):
    """
    ユーザーのミニゲーム用口座情報を取得する。

    Args:
        user_id: LINE user ID

    Returns:
        登録済みの場合: Account オブジェクト
        未登録の場合: None
    """
    db = SessionLocal()
    try:
        # ミニゲーム口座レコードを取得
        minigame_acc = db.execute(
            select(MinigameAccount).filter_by(user_id=user_id, is_active=True)
        ).scalars().first()

        if not minigame_acc:
            return None

        # 関連する口座情報を取得
        account = db.execute(
            select(Account).filter_by(account_id=minigame_acc.account_id)
        ).scalars().first()

        # 最終使用日時を更新
        try:
            minigame_acc.last_used_at = datetime.datetime.now()
            db.commit()
        except Exception:
            db.rollback()

        return account

    except Exception as e:
        print(f"[BankService] get_minigame_account error: {e}")
        return None
    finally:
        db.close()


def get_minigame_account_info(user_id: str):
    """
    ユーザーのミニゲーム用口座の詳細情報を辞書で取得する。

    Args:
        user_id: LINE user ID

    Returns:
        登録済みの場合: dict (account_number, balance, currency, status, etc.)
        未登録の場合: None
    """
    db = SessionLocal()
    try:
        # ミニゲーム口座レコードを取得
        minigame_acc = db.execute(
            select(MinigameAccount).filter_by(user_id=user_id, is_active=True)
        ).scalars().first()

        if not minigame_acc:
            return None

        # 関連する口座情報を取得
        account = db.execute(
            select(Account).filter_by(account_id=minigame_acc.account_id)
        ).scalars().first()

        if not account:
            return None

        # 支店情報を取得
        branch_code = None
        branch_name = None
        try:
            if getattr(account, 'branch', None):
                branch_code = getattr(account.branch, 'code', None)
                branch_name = getattr(account.branch, 'name', None)
        except Exception:
            pass

        balance = getattr(account, 'balance', None)
        balance_str = format(balance, '.2f') if balance is not None else None

        return {
            'account_id': getattr(account, 'account_id', None),
            'account_number': getattr(account, 'account_number', None),
            'balance': balance_str,
            'currency': getattr(account, 'currency', None),
            'type': getattr(account, 'type', None),
            'branch_code': branch_code,
            'branch_name': branch_name,
            'status': getattr(account, 'status', None),
            'registered_at': getattr(minigame_acc, 'registered_at', None),
            'last_used_at': getattr(minigame_acc, 'last_used_at', None),
        }

    except Exception as e:
        print(f"[BankService] get_minigame_account_info error: {e}")
        return None
    finally:
        db.close()


def unregister_minigame_account(user_id: str) -> dict:
    """
    ユーザーのミニゲーム用口座登録を解除する（is_active を False にする）。

    Args:
        user_id: LINE user ID

    Returns:
        {'success': True/False, 'message': str}
    """
    db = SessionLocal()
    try:
        with db.begin():
            minigame_acc = db.execute(
                select(MinigameAccount).filter_by(user_id=user_id, is_active=True)
            ).scalars().first()

            if not minigame_acc:
                return {'success': False, 'message': 'ミニゲーム用口座が登録されていません。'}

            minigame_acc.is_active = False
            db.flush()

            return {'success': True, 'message': 'ミニゲーム用口座の登録を解除しました。'}

    except Exception as e:
        db.rollback()
        print(f"[BankService] unregister_minigame_account error: {e}")
        return {'success': False, 'message': f'解除中にエラーが発生しました: {str(e)}'}
    finally:
        db.close()
