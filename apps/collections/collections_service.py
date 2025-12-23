from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Dict, Optional, List

from sqlalchemy import select, func

import config
from apps.banking.main_bank_system import SessionLocal, Account
from apps.collections.models import CreditProfile, CollectionsCase, CollectionsAccrual, CollectionsEvent
from apps.tax.models import TaxAssessment
from apps.loans.models import Loan
from apps.utilities.timezone_utils import now_jst


def _as_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def get_or_create_credit_profile(db, user_id: str) -> CreditProfile:
    p = db.execute(select(CreditProfile).where(CreditProfile.user_id == user_id)).scalars().first()
    if p:
        return p
    p = CreditProfile(user_id=user_id, is_blacklisted=False)
    db.add(p)
    db.flush()
    return p


def is_blacklisted(user_id: str) -> bool:
    db = SessionLocal()
    try:
        p = db.execute(select(CreditProfile).where(CreditProfile.user_id == user_id)).scalars().first()
        return bool(p and p.is_blacklisted)
    finally:
        db.close()


def set_blacklisted(db, user_id: str, reason: str):
    p = get_or_create_credit_profile(db, user_id)
    if p.is_blacklisted:
        return
    p.is_blacklisted = True
    p.blacklisted_at = now_jst()
    p.blacklisted_reason = reason
    p.updated_at = now_jst()
    db.add(p)


def add_event(db, case_id: int, event_type: str, note: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
    ev = CollectionsEvent(case_id=case_id, event_type=event_type, note=note, meta_json=meta)
    db.add(ev)


def ensure_case(
    *,
    db,
    user_id: str,
    case_type: str,
    reference_id: int,
    status: str,
    due_at: Optional[datetime] = None,
    payment_window_end_at: Optional[datetime] = None,
) -> CollectionsCase:
    c = db.execute(
        select(CollectionsCase).where(CollectionsCase.case_type == case_type, CollectionsCase.reference_id == reference_id)
    ).scalars().first()
    if c:
        return c

    c = CollectionsCase(
        user_id=user_id,
        case_type=case_type,
        reference_id=reference_id,
        status=status,
        due_at=due_at,
        payment_window_end_at=payment_window_end_at,
    )
    db.add(c)
    db.flush()
    add_event(db, c.case_id, 'case_created', meta={'case_type': case_type, 'reference_id': reference_id})
    return c


def ensure_tax_case_for_assessment(*, db, user_id: str, assessment_id: int, due_at: datetime, payment_window_end_at: datetime) -> CollectionsCase:
    return ensure_case(
        db=db,
        user_id=user_id,
        case_type='tax',
        reference_id=assessment_id,
        status='in_payment_window',
        due_at=due_at,
        payment_window_end_at=payment_window_end_at,
    )


def ensure_loan_case_for_loan(*, db, user_id: str, loan_id: int, failed_since: datetime) -> CollectionsCase:
    c = ensure_case(
        db=db,
        user_id=user_id,
        case_type='loan',
        reference_id=loan_id,
        status='overdue',
    )
    if not c.overdue_started_at:
        c.overdue_started_at = failed_since
    db.add(c)
    return c


def mark_case_resolved_if_exists(db, *, case_type: str, reference_id: int, note: str):
    c = db.execute(
        select(CollectionsCase).where(CollectionsCase.case_type == case_type, CollectionsCase.reference_id == reference_id)
    ).scalars().first()
    if not c:
        return
    c.status = 'resolved'
    c.resolved_at = now_jst()
    db.add(c)
    add_event(db, c.case_id, 'case_resolved', note=note)


def get_inline_notice_text(user_id: str, now: Optional[datetime] = None) -> Optional[str]:
    now = now or now_jst()
    db = SessionLocal()
    try:
        cases = db.execute(
            select(CollectionsCase)
            .where(CollectionsCase.user_id == user_id)
            .where(CollectionsCase.status.in_(['overdue', 'seizure']))
        ).scalars().all()

        if not cases:
            # loan overdue>=7 のために overdueケース自体はあるが、7日未満なら出さない
            pending_loan = db.execute(
                select(CollectionsCase)
                .where(CollectionsCase.user_id == user_id)
                .where(CollectionsCase.case_type == 'loan')
                .where(CollectionsCase.status == 'overdue')
            ).scalars().all()
            if not pending_loan:
                return None

        # tax: 即表示
        for c in cases:
            if c.case_type == 'tax':
                return '⚠️ 納税が未完了です。?納税 で確認/納付してください。'

        # loan: 7日目以降で表示
        for c in db.execute(
            select(CollectionsCase)
            .where(CollectionsCase.user_id == user_id)
            .where(CollectionsCase.case_type == 'loan')
            .where(CollectionsCase.status == 'overdue')
        ).scalars().all():
            if not c.overdue_started_at:
                continue
            if (now - c.overdue_started_at).days >= 7:
                return '⚠️ 借金の返済が滞っています。?返済 で返済してください。'

        return None
    finally:
        db.close()


def _latest_accrual_end_date(db, case_id: int) -> Optional[date]:
    d = db.execute(
        select(func.max(CollectionsAccrual.end_date)).where(CollectionsAccrual.case_id == case_id)
    ).scalar_one()
    return d


def accrue_tax_penalty(db, *, case: CollectionsCase, principal: Decimal, up_to: date) -> int:
    """tax_penalty を日次で増分計上（監査ログ）。

    Returns: 計上した日数
    """
    last_end = _latest_accrual_end_date(db, case.case_id)
    start = (last_end + timedelta(days=1)) if last_end else (case.overdue_started_at.date() if case.overdue_started_at else up_to)
    if start > up_to:
        return 0

    days = (up_to - start).days + 1
    weekly_rate = _as_decimal(getattr(config, 'TAX_PENALTY_WEEKLY_RATE', Decimal('0.15')))
    amount = (principal * weekly_rate * Decimal(days)) / Decimal('7')

    acc = CollectionsAccrual(
        case_id=case.case_id,
        accrual_type='tax_penalty',
        amount=amount,
        principal_base=principal,
        start_date=start,
        end_date=up_to,
        days=days,
        note='daily_accrual',
    )
    db.add(acc)
    add_event(db, case.case_id, 'accrual_added', meta={'type': 'tax_penalty', 'days': days, 'start': str(start), 'end': str(up_to)})
    return days


def _round_down_1000(v: Decimal) -> Decimal:
    unit = Decimal('1000')
    return (v // unit) * unit


def compute_case_amount_due(db, case: CollectionsCase) -> Decimal:
    if case.case_type == 'tax':
        a = db.execute(select(TaxAssessment).where(TaxAssessment.assessment_id == case.reference_id)).scalars().first()
        base = _as_decimal(a.tax_amount) if a else Decimal('0')
    else:
        loan = db.execute(select(Loan).where(Loan.loan_id == case.reference_id)).scalars().first()
        base = _as_decimal(loan.outstanding_balance) if loan else Decimal('0')

    penalties = db.execute(
        select(func.coalesce(func.sum(CollectionsAccrual.amount), 0)).where(CollectionsAccrual.case_id == case.case_id)
    ).scalar_one()

    return base + _as_decimal(penalties)


def _seize_bank_balances(db, *, user_id: str, dest_account_number: str, amount_needed: Decimal) -> Decimal:
    from apps.banking.bank_service import transfer_funds

    seized = Decimal('0')
    accounts = db.execute(select(Account).where(Account.user_id == user_id)).scalars().all()

    for acc in accounts:
        if amount_needed <= 0:
            break

        # 凍結
        if getattr(acc, 'status', None) != 'frozen':
            acc.status = 'frozen'
            db.add(acc)

        bal = _as_decimal(getattr(acc, 'balance', 0))
        if bal <= 0:
            continue

        take = bal if bal < amount_needed else amount_needed
        try:
            transfer_funds(
                from_account_number=acc.account_number,
                to_account_number=dest_account_number,
                amount=take,
                currency='JPY',
                description='差押えによる回収',
            )
            seized += take
            amount_needed -= take
        except Exception as e:
            print(f"[Collections] seizure transfer failed user={user_id} from={acc.account_number} err={e}")
            continue

    return seized


def process_collections_daily(run_at: Optional[datetime] = None) -> Dict[str, Any]:
    """日次の回収処理（延滞化・延滞税/遅延利息増分・ブラックリスト・差押え）。"""
    run_at = run_at or now_jst()
    today = run_at.date()

    db = SessionLocal()
    transitioned_overdue = 0
    accrued_cases = 0
    seizures = 0

    try:
        with db.begin():
            cases = db.execute(
                select(CollectionsCase).where(CollectionsCase.status.in_(['in_payment_window', 'overdue', 'seizure']))
            ).scalars().all()

            for c in cases:
                # 税: 期限超過で overdue
                if c.case_type == 'tax' and c.status == 'in_payment_window' and c.payment_window_end_at and run_at > c.payment_window_end_at:
                    c.status = 'overdue'
                    c.overdue_started_at = run_at
                    transitioned_overdue += 1
                    db.add(c)
                    add_event(db, c.case_id, 'became_overdue')
                    # ルール単純化: 未納税状態=ブラックリスト
                    set_blacklisted(db, c.user_id, reason='tax_overdue')
                    c.blacklisted_at = run_at

                # ローン: overdue中で7日経過したらブラックリスト
                if c.case_type == 'loan' and c.status == 'overdue' and c.overdue_started_at and not c.blacklisted_at:
                    if (run_at - c.overdue_started_at).days >= 7:
                        set_blacklisted(db, c.user_id, reason='loan_overdue')
                        c.blacklisted_at = run_at
                        add_event(db, c.case_id, 'blacklisted')
                        db.add(c)

                # ローン: 14日経過で差押え
                if c.case_type == 'loan' and c.status == 'overdue' and c.overdue_started_at:
                    if (run_at - c.overdue_started_at).days >= int(getattr(config, 'TAX_SEIZURE_DAYS', 14)):
                        c.status = 'seizure'
                        c.seizure_started_at = run_at
                        db.add(c)
                        add_event(db, c.case_id, 'seizure_started')

                # tax penalty accrual
                if c.case_type == 'tax' and c.status in ('overdue', 'seizure') and c.overdue_started_at:
                    assessment = db.execute(select(TaxAssessment).where(TaxAssessment.assessment_id == c.reference_id)).scalars().first()
                    if assessment and assessment.status == 'paid':
                        c.status = 'resolved'
                        c.resolved_at = run_at
                        db.add(c)
                        add_event(db, c.case_id, 'resolved_by_payment')
                        continue

                    principal = _round_down_1000(_as_decimal(assessment.tax_amount if assessment else 0))
                    if principal > 0:
                        days_added = accrue_tax_penalty(db, case=c, principal=principal, up_to=today - timedelta(days=1))
                        if days_added:
                            accrued_cases += 1

                    # 滞納2週間で差押え
                    if c.status != 'seizure' and (run_at - c.overdue_started_at).days >= int(getattr(config, 'TAX_SEIZURE_DAYS', 14)):
                        c.status = 'seizure'
                        c.seizure_started_at = run_at
                        db.add(c)
                        add_event(db, c.case_id, 'seizure_started')

                # 差押え実行（税/ローン共通で、まず銀行残高から）
                if c.status == 'seizure':
                    amount_due = compute_case_amount_due(db, c)
                    if amount_due <= 0:
                        c.status = 'resolved'
                        c.resolved_at = run_at
                        db.add(c)
                        add_event(db, c.case_id, 'resolved_no_due')
                        continue

                    dest = getattr(config, 'TAX_DEST_ACCOUNT_NUMBER', '1111111') if c.case_type == 'tax' else getattr(config, 'LOAN_LENDER_ACCOUNT_NUMBER', '7777777')
                    seized = _seize_bank_balances(db, user_id=c.user_id, dest_account_number=dest, amount_needed=amount_due)
                    if seized > 0:
                        seizures += 1
                        add_event(db, c.case_id, 'seizure_collected', meta={'seized': str(seized)})

        return {
            'success': True,
            'transitioned_overdue': transitioned_overdue,
            'accrued_cases': accrued_cases,
            'seizures': seizures,
        }
    except Exception as e:
        db.rollback()
        print(f"[Collections] process_collections_daily failed err={e}")
        raise
    finally:
        db.close()
