from __future__ import annotations

from decimal import Decimal
from typing import Optional, Dict, Any

from linebot.models import TextSendMessage
from sqlalchemy import select

from apps.banking.main_bank_system import SessionLocal, Account, Branch
from apps.tax.models import TaxProfile, TaxAssessment
from apps.utilities.timezone_utils import now_jst, format_jst
from apps.tax.tax_service import _as_decimal


def _tax_status_ja(status: Any) -> str:
    s = str(status) if status is not None else ''
    mapping = {
        'assessed': '未納',
        'paid': '納付済み',
    }
    return mapping.get(s, s or '-')


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


def _ensure_profile(db, user_id: str) -> TaxProfile:
    p = db.execute(select(TaxProfile).where(TaxProfile.user_id == user_id)).scalars().first()
    if p:
        return p
    p = TaxProfile(user_id=user_id)
    db.add(p)
    db.flush()
    return p


def _latest_assessment(db, user_id: str) -> Optional[TaxAssessment]:
    return db.execute(
        select(TaxAssessment)
        .where(TaxAssessment.user_id == user_id)
        .order_by(TaxAssessment.assessment_id.desc())
        .limit(1)
    ).scalars().first()


def handle_tax_command(user_id: str, text: str) -> TextSendMessage:
    """`?納税` コマンド。

    - `?納税` : 状態表示
    - `?納税 設定 001-1234567` : 納税口座設定
    - `?納税 納付` : 自動納税口座から手動納付（当週の未納があれば）
    """
    parts = text.strip().split()

    db = SessionLocal()
    try:
        with db.begin():
            profile = _ensure_profile(db, user_id)

            if len(parts) >= 3 and parts[1] == '設定':
                token = parts[2]
                if '-' not in token:
                    return TextSendMessage(text='形式: ?納税 設定 001-1234567')
                branch_code, acct_no = token.split('-', 1)
                acc = _find_account_by_branch_and_number(db, branch_code, acct_no, user_id)
                if not acc:
                    return TextSendMessage(text='指定口座が見つかりません（あなた名義の口座のみ設定できます）')
                profile.tax_account_id = acc.account_id
                profile.updated_at = now_jst()
                db.add(profile)
                return TextSendMessage(text=f'納税口座を設定しました: {branch_code}-{acct_no}')

        # ここからはトランザクション外（納付時にbank transferを呼ぶため）
        if len(parts) >= 2 and parts[1] == '納付':
            from apps.tax.tax_service import pay_latest_unpaid_tax
            result = pay_latest_unpaid_tax(user_id)
            if result.get('success'):
                return TextSendMessage(text=f"納付しました: ¥{int(Decimal(result['amount'])):,}")
            return TextSendMessage(text=result.get('message', '納付できませんでした'))

        # 表示
        db2 = SessionLocal()
        try:
            profile2 = db2.execute(select(TaxProfile).where(TaxProfile.user_id == user_id)).scalars().first()
            a = _latest_assessment(db2, user_id)

            acct_text = '未設定'
            if profile2 and profile2.tax_account_id:
                acc = db2.execute(select(Account).where(Account.account_id == profile2.tax_account_id)).scalars().first()
                if acc:
                    br = db2.execute(select(Branch).where(Branch.branch_id == acc.branch_id)).scalars().first()
                    acct_text = f"{br.code if br else '???'}-{acc.account_number}" if acc else '未設定'

            if not a:
                return TextSendMessage(text=f"【納税】\n納税口座: {acct_text}\n今週の課税はまだ確定していません")

            status = a.status
            tax_amount = _as_decimal(a.tax_amount)
            msg = (
                "【納税】\n"
                f"納税口座: {acct_text}\n"
                f"税額: ¥{int(tax_amount):,}\n"
                f"状態: {_tax_status_ja(status)}\n"
                f"納付期限: {format_jst(a.payment_window_end_at, '%m/%d %H:%M')}\n"
            )
            if status != 'paid' and tax_amount > 0:
                msg += "納付: ?納税 納付\n設定: ?納税 設定 001-1234567"
            return TextSendMessage(text=msg)
        finally:
            db2.close()

    finally:
        db.close()
