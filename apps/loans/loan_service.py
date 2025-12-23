from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select

import config
from apps.banking.main_bank_system import SessionLocal, Account
from apps.loans.models import Loan, LoanPayment
from apps.utilities.timezone_utils import now_jst


def _as_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def compute_interest_rate(principal: Decimal, prev_week_income: Decimal) -> Tuple[Decimal, Decimal]:
    """仕様: (principal / prev_income) * 0.04% をベースに、上限(cap)を適用。"""
    base_factor = _as_decimal(getattr(config, 'LOAN_INTEREST_FACTOR', '0.0004'))  # 0.04%

    if prev_week_income <= 0:
        return Decimal('0'), Decimal('0')

    raw = (principal / prev_week_income) * base_factor
    cap = _as_decimal(getattr(config, 'LOAN_INTEREST_RATE_CAP', '0.02'))
    applied = raw if raw <= cap else cap
    return raw, applied


def can_borrow(user_id: str, amount: Decimal, reference_at: Optional[datetime] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """借入可否判定（ルールはブラックリスト中心に単純化）。"""
    from apps.collections.collections_service import is_blacklisted
    from apps.tax.tax_service import get_prev_week_total_income

    amount = _as_decimal(amount)
    if amount < _as_decimal(getattr(config, 'LOAN_MIN_PRINCIPAL', 10000)):
        return False, '借入は1万円からです', {}

    if is_blacklisted(user_id):
        return False, 'ブラックリストのため借入できません', {}

    income = get_prev_week_total_income(user_id, reference_at)
    if income <= 0:
        return False, '前週所得が0のため借入できません', {'prev_week_income': str(income)}

    max_amount = income * _as_decimal(getattr(config, 'LOAN_MAX_MULTIPLIER', 5))
    if amount > max_amount:
        return False, f'借入上限は前週所得の{getattr(config, "LOAN_MAX_MULTIPLIER", 5)}倍までです', {
            'prev_week_income': str(income),
            'max_amount': str(max_amount),
        }

    raw_rate, applied_rate = compute_interest_rate(amount, income)
    return True, 'ok', {
        'prev_week_income': str(income),
        'max_amount': str(max_amount),
        'raw_rate': str(raw_rate),
        'applied_rate': str(applied_rate),
    }


def create_loan(user_id: str, principal: Any, receive_account_id: int, autopay_account_id: int, autopay_amount: Any = 1000) -> Dict[str, Any]:
    """ローンを発行し、準備口座からユーザー口座へ振り込む。"""
    principal = _as_decimal(principal)
    autopay_amount = _as_decimal(autopay_amount)

    ok, msg, meta = can_borrow(user_id, principal)
    if not ok:
        return {'success': False, 'message': msg, 'meta': meta}

    raw_rate = _as_decimal(meta['raw_rate'])
    applied_rate = _as_decimal(meta['applied_rate'])

    db = SessionLocal()
    try:
        recv_acc = db.execute(select(Account).where(Account.account_id == receive_account_id)).scalars().first()
        auto_acc = db.execute(select(Account).where(Account.account_id == autopay_account_id)).scalars().first()
        if not recv_acc or recv_acc.user_id != user_id:
            return {'success': False, 'message': '受取口座が見つかりません'}
        if not auto_acc or auto_acc.user_id != user_id:
            return {'success': False, 'message': '自動引落口座が見つかりません'}

        with db.begin():
            loan = Loan(
                user_id=user_id,
                principal=principal,
                outstanding_balance=principal,
                status='active',
                interest_weekly_rate=raw_rate,
                interest_weekly_rate_cap_applied=applied_rate,
                late_interest_weekly_rate=_as_decimal(getattr(config, 'LOAN_LATE_WEEKLY_RATE', '0.20')),
                autopay_account_id=autopay_account_id,
                autopay_amount=autopay_amount,
            )
            db.add(loan)
            db.flush()
            loan_id = loan.loan_id

        # 振込（別トランザクション）
        from apps.banking.bank_service import transfer_funds, RESERVE_ACCOUNT_NUMBER

        try:
            tx = transfer_funds(
                from_account_number=RESERVE_ACCOUNT_NUMBER,
                to_account_number=recv_acc.account_number,
                amount=principal,
                currency='JPY',
                description='借入',
            )
        except Exception as e:
            # 失敗したらローンを無効化
            db2 = SessionLocal()
            try:
                with db2.begin():
                    l = db2.execute(select(Loan).where(Loan.loan_id == loan_id)).scalars().first()
                    if l:
                        l.status = 'resolved'
                        l.outstanding_balance = Decimal('0')
                        db2.add(l)
            finally:
                db2.close()
            return {'success': False, 'message': f'振込に失敗しました: {e}'}

        return {
            'success': True,
            'loan_id': loan_id,
            'transaction_id': tx.get('transaction_id'),
            'principal': str(principal),
            'interest_rate': str(applied_rate),
        }
    finally:
        db.close()


def accrue_daily_interest(run_at: Optional[datetime] = None) -> Dict[str, Any]:
    """ローン利息を日次で積み上げる（監査ログはcollections側で残す）。"""
    run_at = run_at or now_jst()
    db = SessionLocal()
    updated = 0
    try:
        with db.begin():
            loans = db.execute(select(Loan).where(Loan.status == 'active')).scalars().all()
            for loan in loans:
                bal = _as_decimal(loan.outstanding_balance)
                if bal <= 0:
                    continue

                # 延滞中は遅延損害金（週20%日割り）
                weekly_rate = _as_decimal(loan.interest_weekly_rate_cap_applied)
                if loan.autopay_failed_since:
                    weekly_rate = _as_decimal(loan.late_interest_weekly_rate)

                daily_rate = weekly_rate / Decimal('7')
                interest = (bal * daily_rate)
                if interest <= 0:
                    continue

                loan.outstanding_balance = bal + interest
                loan.updated_at = run_at
                db.add(loan)

                # 監査ログ（collections）
                from apps.collections.collections_service import ensure_case, add_event
                c = ensure_case(db=db, user_id=loan.user_id, case_type='loan', reference_id=loan.loan_id, status='open')
                add_event(db, c.case_id, 'loan_interest_accrued', meta={'interest': str(interest), 'daily_rate': str(daily_rate)})
                updated += 1

        return {'success': True, 'updated': updated}
    except Exception as e:
        db.rollback()
        print(f"[LoanService] accrue_daily_interest failed err={e}")
        raise
    finally:
        db.close()


def manual_repay(user_id: str, amount: Any) -> Dict[str, Any]:
    """手動返済（デフォルト: そのユーザーの最初の口座から準備預金口座へ送金）。"""
    amount = _as_decimal(amount)
    if amount <= 0:
        return {'success': False, 'message': '返済額が不正です'}

    # 1000円単位
    if (amount % Decimal('1000')) != 0:
        return {'success': False, 'message': '返済は1000円単位です'}

    db = SessionLocal()
    try:
        loan = db.execute(
            select(Loan)
            .where(Loan.user_id == user_id)
            .where(Loan.status == 'active')
            .order_by(Loan.loan_id.desc())
            .limit(1)
        ).scalars().first()
        if not loan:
            return {'success': False, 'message': '返済対象のローンがありません'}

        from_acc = db.execute(
            select(Account)
            .where(Account.user_id == user_id)
            .where(Account.status.in_(['active', 'frozen']))
            .order_by(Account.account_id.asc())
            .limit(1)
        ).scalars().first()
        if not from_acc:
            return {'success': False, 'message': '返済元口座が見つかりません'}

        bal = _as_decimal(loan.outstanding_balance)
        pay_amount = amount if amount < bal else bal

        from apps.banking.bank_service import transfer_funds, RESERVE_ACCOUNT_NUMBER
        try:
            tx = transfer_funds(
                from_account_number=from_acc.account_number,
                to_account_number=RESERVE_ACCOUNT_NUMBER,
                amount=pay_amount,
                currency='JPY',
                description='借金返済（手動）',
            )
        except Exception as e:
            return {'success': False, 'message': f'振込に失敗しました: {e}'}

        with db.begin():
            loan.outstanding_balance = bal - pay_amount
            loan.updated_at = now_jst()
            # 手動返済が入ったら延滞状態は解除
            loan.autopay_failed_since = None
            db.add(loan)

            lp = LoanPayment(
                loan_id=loan.loan_id,
                bank_transaction_id=tx.get('transaction_id') if isinstance(tx, dict) else None,
                amount=pay_amount,
                paid_at=now_jst(),
            )
            db.add(lp)

            if _as_decimal(loan.outstanding_balance) <= 0:
                loan.status = 'resolved'
                db.add(loan)
                from apps.collections.collections_service import mark_case_resolved_if_exists
                mark_case_resolved_if_exists(db, case_type='loan', reference_id=loan.loan_id, note='manual_paid_off')

        return {'success': True, 'paid': str(pay_amount), 'remaining_balance': str(_as_decimal(loan.outstanding_balance))}
    finally:
        db.close()


def attempt_autopay_daily(run_at: Optional[datetime] = None) -> Dict[str, Any]:
    """日次の自動引落（失敗時は7日間再挑戦+Push、7日後から全発言督促+ブラックリスト、14日後差押えはcollectionsが担当）。"""
    run_at = run_at or now_jst()

    from apps.banking.bank_service import transfer_funds, RESERVE_ACCOUNT_NUMBER
    from core.api import line_bot_api

    db = SessionLocal()
    attempted = 0
    paid = 0
    failed = 0

    try:
        loans = db.execute(select(Loan).where(Loan.status == 'active')).scalars().all()
        for loan in loans:
            bal = _as_decimal(loan.outstanding_balance)
            if bal <= 0:
                continue
            if not loan.autopay_account_id:
                continue

            auto_acc = db.execute(select(Account).where(Account.account_id == loan.autopay_account_id)).scalars().first()
            if not auto_acc:
                continue

            amount = _as_decimal(loan.autopay_amount)
            if amount <= 0:
                continue

            pay_amount = amount if amount < bal else bal

            attempted += 1
            try:
                tx = transfer_funds(
                    from_account_number=auto_acc.account_number,
                    to_account_number=RESERVE_ACCOUNT_NUMBER,
                    amount=pay_amount,
                    currency='JPY',
                    description='借金返済（自動）',
                )

                with db.begin():
                    loan.outstanding_balance = bal - pay_amount
                    loan.last_autopay_attempt_at = run_at
                    loan.autopay_failed_since = None
                    loan.updated_at = run_at
                    db.add(loan)

                    lp = LoanPayment(
                        loan_id=loan.loan_id,
                        bank_transaction_id=tx.get('transaction_id'),
                        amount=pay_amount,
                        paid_at=run_at,
                    )
                    db.add(lp)

                    if loan.outstanding_balance <= 0:
                        loan.status = 'resolved'
                        db.add(loan)

                        from apps.collections.collections_service import mark_case_resolved_if_exists
                        mark_case_resolved_if_exists(db, case_type='loan', reference_id=loan.loan_id, note='paid_off')

                paid += 1

            except Exception as e:
                failed += 1
                with db.begin():
                    loan.last_autopay_attempt_at = run_at
                    if not loan.autopay_failed_since:
                        loan.autopay_failed_since = run_at
                    db.add(loan)

                    from apps.collections.collections_service import ensure_loan_case_for_loan, add_event
                    c = ensure_loan_case_for_loan(db=db, user_id=loan.user_id, loan_id=loan.loan_id, failed_since=loan.autopay_failed_since)
                    add_event(db, c.case_id, 'autopay_failed', note=str(e))

                # 2日に1回Push（個別チャット前提）
                failed_since = loan.autopay_failed_since
                if failed_since and (run_at - failed_since).days <= 7:
                    if (run_at - failed_since).days % 2 == 0:
                        try:
                            line_bot_api.push_message(
                                loan.user_id,
                                [
                                    {
                                        'type': 'text',
                                        'text': '⚠️ 借金の自動引落に失敗しました。残高不足などを確認し、?返済 で返済してください。',
                                    }
                                ],
                            )
                        except Exception as push_err:
                            print(f"[LoanService] push failed user={loan.user_id} err={push_err}")

        return {'success': True, 'attempted': attempted, 'paid': paid, 'failed': failed}
    finally:
        db.close()
