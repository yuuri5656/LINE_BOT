from __future__ import annotations

from decimal import Decimal
from typing import Optional

from linebot.models import TextSendMessage
from sqlalchemy import select

from apps.banking.main_bank_system import SessionLocal, Account, Branch
from apps.loans.models import Loan
from apps.utilities.timezone_utils import format_jst


def _find_account_by_branch_and_number(db, branch_code: str, account_number: str, user_id: str) -> Optional[Account]:
    branch = db.execute(select(Branch).where(Branch.code == str(branch_code))).scalars().first()
    if not branch:
        return None
    return db.execute(
        select(Account)
        .where(Account.branch_id == branch.branch_id)
        .where(Account.account_number == str(account_number))
        .where(Account.user_id == user_id)
    ).scalars().first()


def _get_default_account(db, user_id: str) -> Optional[Account]:
    return db.execute(
        select(Account)
        .where(Account.user_id == user_id)
        .where(Account.status.in_(['active', 'frozen']))
        .order_by(Account.account_id.asc())
        .limit(1)
    ).scalars().first()


def _latest_active_loan(db, user_id: str) -> Optional[Loan]:
    return db.execute(
        select(Loan)
        .where(Loan.user_id == user_id)
        .where(Loan.status == 'active')
        .order_by(Loan.loan_id.desc())
        .limit(1)
    ).scalars().first()


def handle_loan_command(user_id: str, text: str) -> TextSendMessage:
    """ローン関連。

    - `?借入 50000` : 借入（受取/自動引落はデフォルト口座）
    - `?返済` : 状態表示
    - `?返済 5000` : 返済（デフォルト口座から）
    - `?返済 設定 001-1234567` : 自動引落口座の変更
    """
    parts = text.strip().split()
    cmd = parts[0]

    db = SessionLocal()
    try:
        if cmd == '?借入':
            if len(parts) < 2:
                return TextSendMessage(text='形式: ?借入 50000')
            amount = Decimal(parts[1])

            acc = _get_default_account(db, user_id)
            if not acc:
                return TextSendMessage(text='口座が見つかりません')

            from apps.loans.loan_service import create_loan
            result = create_loan(
                user_id=user_id,
                principal=amount,
                receive_account_id=acc.account_id,
                autopay_account_id=acc.account_id,
                autopay_amount=Decimal('1000'),
            )
            if not result.get('success'):
                return TextSendMessage(text=result.get('message', '借入できませんでした'))
            return TextSendMessage(text=f"借入しました: ¥{int(amount):,}\nローンID: {result['loan_id']}")

        if cmd == '?返済':
            # 設定変更
            if len(parts) >= 3 and parts[1] == '設定':
                token = parts[2]
                if '-' not in token:
                    return TextSendMessage(text='形式: ?返済 設定 001-1234567')
                branch_code, acct_no = token.split('-', 1)
                acc = _find_account_by_branch_and_number(db, branch_code, acct_no, user_id)
                if not acc:
                    return TextSendMessage(text='指定口座が見つかりません')

                loan = _latest_active_loan(db, user_id)
                if not loan:
                    return TextSendMessage(text='返済対象のローンがありません')

                with db.begin():
                    loan.autopay_account_id = acc.account_id
                    db.add(loan)

                return TextSendMessage(text=f'自動引落口座を設定しました: {branch_code}-{acct_no}')

            # 返済実行
            if len(parts) >= 2:
                amount = Decimal(parts[1])
                from apps.loans.loan_service import manual_repay
                result = manual_repay(user_id=user_id, amount=amount)
                if result.get('success'):
                    return TextSendMessage(text=f"返済しました: ¥{int(amount):,}\n残高: ¥{int(Decimal(result['remaining_balance'])):,}")
                return TextSendMessage(text=result.get('message', '返済できませんでした'))

            # 状態表示
            loan = _latest_active_loan(db, user_id)
            if not loan:
                return TextSendMessage(text='返済対象のローンがありません')

            bal = Decimal(str(loan.outstanding_balance))
            msg = (
                "【借金】\n"
                f"残高: ¥{int(bal):,}\n"
                f"自動引落: ¥{int(Decimal(str(loan.autopay_amount))):,}/日\n"
            )
            if loan.last_autopay_attempt_at:
                msg += f"最終試行: {format_jst(loan.last_autopay_attempt_at, '%m/%d %H:%M')}\n"
            if loan.autopay_failed_since:
                msg += f"失敗開始: {format_jst(loan.autopay_failed_since, '%m/%d %H:%M')}\n"
            msg += "返済: ?返済 5000\n自動引落変更: ?返済 設定 001-1234567"
            return TextSendMessage(text=msg)

        return TextSendMessage(text='不明なコマンドです')
    finally:
        db.close()
