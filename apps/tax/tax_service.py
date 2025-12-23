from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import Any, Optional, Dict, Tuple, List

from sqlalchemy import select, func

import config
from apps.banking.main_bank_system import SessionLocal, Account
from apps.tax.models import TaxProfile, TaxPeriod, TaxIncomeEvent, TaxAssessment, TaxPayment
from apps.utilities.timezone_utils import now_jst


@dataclass(frozen=True)
class TaxBracket:
    min_income: Decimal
    max_income: Optional[Decimal]  # None means no upper bound
    rate: Decimal
    deduction: Decimal


def _as_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _load_brackets_from_config() -> List[TaxBracket]:
    brackets = []
    for b in getattr(config, 'TAX_BRACKETS', []):
        brackets.append(
            TaxBracket(
                min_income=_as_decimal(b['min']),
                max_income=_as_decimal(b['max']) if b.get('max') is not None else None,
                rate=_as_decimal(b['rate']),
                deduction=_as_decimal(b['deduction']),
            )
        )
    return brackets


def compute_tax_amount(weekly_income: Decimal) -> Tuple[Decimal, Decimal]:
    """週所得から (課税所得, 税額) を返す。

    仕様:
    - 1万円未満は非課税
    - 課税所得は1000円未満切捨て
    - 税額 = 課税所得×税率 - 控除額（0未満なら0）
    """
    weekly_income = _as_decimal(weekly_income)

    if weekly_income < _as_decimal(getattr(config, 'TAX_NON_TAXABLE_THRESHOLD', 10000)):
        return Decimal('0'), Decimal('0')

    unit = _as_decimal(getattr(config, 'TAX_ROUND_UNIT', 1000))
    taxable = (weekly_income // unit) * unit

    brackets = _load_brackets_from_config()
    for bracket in brackets:
        if taxable < bracket.min_income:
            continue
        if bracket.max_income is None or taxable <= bracket.max_income:
            tax = taxable * bracket.rate - bracket.deduction
            if tax < 0:
                tax = Decimal('0')
            return taxable, tax

    return taxable, Decimal('0')


def get_tax_week_bounds_for_assessment(run_at: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """課税対象となる『前週』の期間 [start, end) を返す。

    実行時刻（通常: 日曜15:00 JST）を基準に、前週は
    日曜15:01〜翌日曜15:01 の半開区間で管理する。
    """
    ref = run_at or now_jst()

    # その週の課税締めは日曜15:01(JST)とする（半開区間のend）
    # 実行は日曜15:00想定なので、endは1分後。
    end = ref.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # start = end - 7日
    start = end - timedelta(days=7)

    return start, end


def get_payment_window_end(due_at: datetime) -> datetime:
    """納付期限（火曜終日）を返す。"""
    # due_at は日曜15:00想定
    # 火曜 23:59:59 JST
    tuesday = (due_at + timedelta(days=2)).date()  # Tue
    return datetime.combine(tuesday, time(23, 59, 59), tzinfo=due_at.tzinfo)


def ensure_tax_period(db, start_at: datetime, end_at: datetime) -> TaxPeriod:
    period = db.execute(
        select(TaxPeriod).where(TaxPeriod.start_at == start_at, TaxPeriod.end_at == end_at)
    ).scalars().first()
    if period:
        return period

    period = TaxPeriod(start_at=start_at, end_at=end_at)
    db.add(period)
    db.flush()
    return period


def record_income_event(
    *,
    user_id: str,
    occurred_at: datetime,
    category: str,
    amount: Any,
    taxable_amount: Any,
    source_type: str,
    source_id: int,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """所得イベントを一意に記録する（再実行に強い）。

    Returns: 新規作成ならTrue、既に存在ならFalse
    """
    db = SessionLocal()
    try:
        existing = db.execute(
            select(TaxIncomeEvent).where(
                TaxIncomeEvent.source_type == source_type,
                TaxIncomeEvent.source_id == source_id,
            )
        ).scalars().first()
        if existing:
            return False

        ev = TaxIncomeEvent(
            user_id=user_id,
            occurred_at=occurred_at,
            category=category,
            amount=_as_decimal(amount),
            taxable_amount=_as_decimal(taxable_amount),
            source_type=source_type,
            source_id=int(source_id),
            meta_json=meta,
        )
        db.add(ev)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"[TaxService] record_income_event failed user={user_id} source={source_type}:{source_id} err={e}")
        raise
    finally:
        db.close()


def record_work_income(*, user_id: str, bank_transaction_id: int, amount: Any, occurred_at: Optional[datetime] = None):
    occurred_at = occurred_at or now_jst()
    record_income_event(
        user_id=user_id,
        occurred_at=occurred_at,
        category='work_salary',
        amount=amount,
        taxable_amount=amount,
        source_type='bank_transaction',
        source_id=bank_transaction_id,
        meta={'description': '労働報酬'},
    )


def record_dividend_income(*, user_id: str, bank_transaction_id: int, amount: Any, symbol_code: str, occurred_at: Optional[datetime] = None):
    occurred_at = occurred_at or now_jst()
    record_income_event(
        user_id=user_id,
        occurred_at=occurred_at,
        category='stock_dividend',
        amount=amount,
        taxable_amount=amount,
        source_type='bank_transaction',
        source_id=bank_transaction_id,
        meta={'symbol_code': symbol_code},
    )


def record_stock_sale_profit(
    *,
    user_id: str,
    stock_transaction_id: int,
    profit: Any,
    proceeds: Any,
    cost_basis: Any,
    bank_transaction_id: Optional[int] = None,
    occurred_at: Optional[datetime] = None,
    symbol_code: Optional[str] = None,
):
    occurred_at = occurred_at or now_jst()
    profit_d = _as_decimal(profit)
    taxable = profit_d if profit_d > 0 else Decimal('0')
    record_income_event(
        user_id=user_id,
        occurred_at=occurred_at,
        category='stock_sale_profit',
        amount=profit_d,
        taxable_amount=taxable,
        source_type='stock_transaction',
        source_id=stock_transaction_id,
        meta={
            'symbol_code': symbol_code,
            'proceeds': str(_as_decimal(proceeds)),
            'cost_basis': str(_as_decimal(cost_basis)),
            'bank_transaction_id': bank_transaction_id,
        },
    )


def record_gamble_cashout_income(
    *,
    user_id: str,
    bank_transaction_id: int,
    cashout_amount: Any,
    occurred_at: Optional[datetime] = None,
    cost_basis: Any = 0,
):
    """ギャンブル所得（換金時）: max(0, cashout - cost_basis - 100000) / 2"""
    occurred_at = occurred_at or now_jst()

    cashout = _as_decimal(cashout_amount)
    cost = _as_decimal(cost_basis)
    special_deduction = _as_decimal(getattr(config, 'GAMBLE_SPECIAL_DEDUCTION', 100000))

    taxable = cashout - cost - special_deduction
    if taxable < 0:
        taxable = Decimal('0')
    taxable = taxable / Decimal('2')

    record_income_event(
        user_id=user_id,
        occurred_at=occurred_at,
        category='gamble_cashout',
        amount=cashout,
        taxable_amount=taxable,
        source_type='bank_transaction',
        source_id=bank_transaction_id,
        meta={
            'formula': 'max(0, cashout - cost_basis - 100000) / 2',
            'cashout': str(cashout),
            'cost_basis': str(cost),
            'special_deduction': str(special_deduction),
        },
    )


def get_prev_week_total_income(user_id: str, reference_at: Optional[datetime] = None) -> Decimal:
    start_at, end_at = get_tax_week_bounds_for_assessment(reference_at or now_jst())

    db = SessionLocal()
    try:
        total = db.execute(
            select(func.coalesce(func.sum(TaxIncomeEvent.amount), 0))
            .where(TaxIncomeEvent.user_id == user_id)
            .where(TaxIncomeEvent.occurred_at >= start_at)
            .where(TaxIncomeEvent.occurred_at < end_at)
        ).scalar_one()
        return _as_decimal(total)
    finally:
        db.close()


def assess_weekly_taxes_and_autopay(run_at: Optional[datetime] = None) -> Dict[str, Any]:
    """週次課税の確定と、自動納税（可能なら）を実行する。"""
    run_at = run_at or now_jst()
    start_at, end_at = get_tax_week_bounds_for_assessment(run_at)

    due_at = run_at.replace(second=0, microsecond=0)
    payment_window_end_at = get_payment_window_end(due_at)

    db = SessionLocal()
    created = 0
    auto_paid = 0
    try:
        with db.begin():
            period = ensure_tax_period(db, start_at, end_at)

            # 対象ユーザー（その週に所得イベントがあるユーザー）
            user_ids = [
                r[0]
                for r in db.execute(
                    select(TaxIncomeEvent.user_id)
                    .where(TaxIncomeEvent.occurred_at >= start_at)
                    .where(TaxIncomeEvent.occurred_at < end_at)
                    .group_by(TaxIncomeEvent.user_id)
                ).all()
            ]

            for user_id in user_ids:
                # 既に課税確定済みならスキップ
                existing = db.execute(
                    select(TaxAssessment).where(
                        TaxAssessment.user_id == user_id,
                        TaxAssessment.period_id == period.period_id,
                    )
                ).scalars().first()
                if existing:
                    continue

                totals = db.execute(
                    select(
                        func.coalesce(func.sum(TaxIncomeEvent.amount), 0),
                        func.coalesce(func.sum(TaxIncomeEvent.taxable_amount), 0),
                    )
                    .where(TaxIncomeEvent.user_id == user_id)
                    .where(TaxIncomeEvent.occurred_at >= start_at)
                    .where(TaxIncomeEvent.occurred_at < end_at)
                ).first()

                total_income = _as_decimal(totals[0])
                weekly_income_for_tax = _as_decimal(totals[1])

                taxable_income, tax_amount = compute_tax_amount(weekly_income_for_tax)

                status = 'paid' if tax_amount == 0 else 'assessed'
                assessment = TaxAssessment(
                    user_id=user_id,
                    period_id=period.period_id,
                    total_income=total_income,
                    taxable_income=taxable_income,
                    tax_amount=tax_amount,
                    status=status,
                    due_at=due_at,
                    payment_window_end_at=payment_window_end_at,
                    paid_at=due_at if tax_amount == 0 else None,
                )
                db.add(assessment)
                db.flush()
                created += 1

                if tax_amount > 0:
                    # 回収ケースを作る（税）
                    from apps.collections.collections_service import ensure_tax_case_for_assessment

                    ensure_tax_case_for_assessment(
                        db=db,
                        user_id=user_id,
                        assessment_id=assessment.assessment_id,
                        due_at=due_at,
                        payment_window_end_at=payment_window_end_at,
                    )

        # 自動納税（別トランザクションで安全に）
        # NOTE: transfer_fundsは内部で独自セッションを使う
        from apps.banking.bank_service import transfer_funds

        db2 = SessionLocal()
        try:
            assessments = db2.execute(
                select(TaxAssessment)
                .where(TaxAssessment.period_id == period.period_id)
                .where(TaxAssessment.tax_amount > 0)
                .where(TaxAssessment.status == 'assessed')
            ).scalars().all()

            for a in assessments:
                profile = db2.execute(select(TaxProfile).where(TaxProfile.user_id == a.user_id)).scalars().first()
                if not profile or not profile.tax_account_id:
                    continue

                from_acc = db2.execute(select(Account).where(Account.account_id == profile.tax_account_id)).scalars().first()
                if not from_acc:
                    continue

                try:
                    tx = transfer_funds(
                        from_account_number=from_acc.account_number,
                        to_account_number=getattr(config, 'TAX_DEST_ACCOUNT_NUMBER', '1111111'),
                        amount=a.tax_amount,
                        currency='JPY',
                        description='所得税（自動納付）',
                    )
                except Exception as e:
                    print(f"[TaxService] autopay failed user={a.user_id} err={e}")
                    continue

                with db2.begin():
                    payment = TaxPayment(
                        assessment_id=a.assessment_id,
                        bank_transaction_id=tx.get('transaction_id'),
                        amount=_as_decimal(a.tax_amount),
                    )
                    db2.add(payment)
                    a.status = 'paid'
                    a.paid_at = run_at
                    db2.add(a)
                    auto_paid += 1

                    from apps.collections.collections_service import mark_case_resolved_if_exists
                    mark_case_resolved_if_exists(db2, case_type='tax', reference_id=a.assessment_id, note='auto_paid')

        finally:
            db2.close()

        return {
            'success': True,
            'period_start': start_at,
            'period_end': end_at,
            'created_assessments': created,
            'auto_paid': auto_paid,
        }
    except Exception as e:
        db.rollback()
        print(f"[TaxService] assess_weekly_taxes_and_autopay failed err={e}")
        raise
    finally:
        db.close()


def set_tax_account_by_branch_and_number(user_id: str, branch_code: str, account_number: str) -> Dict[str, Any]:
    """納税元口座（tax_profiles.tax_account_id）を設定する。"""
    db = SessionLocal()
    try:
        from sqlalchemy import select
        from apps.banking.main_bank_system import Branch

        with db.begin():
            branch = db.execute(select(Branch).where(Branch.code == str(branch_code))).scalars().first()
            if not branch:
                return {'success': False, 'message': '支店が見つかりません'}

            acc = db.execute(
                select(Account)
                .where(Account.branch_id == branch.branch_id)
                .where(Account.account_number == str(account_number))
                .where(Account.user_id == user_id)
            ).scalars().first()
            if not acc:
                return {'success': False, 'message': '口座が見つかりません（あなた名義のみ設定可能）'}

            profile = db.execute(select(TaxProfile).where(TaxProfile.user_id == user_id)).scalars().first()
            if not profile:
                profile = TaxProfile(user_id=user_id)
                db.add(profile)
                db.flush()

            profile.tax_account_id = acc.account_id
            profile.updated_at = now_jst()
            db.add(profile)
            return {'success': True, 'message': 'ok', 'tax_account_id': acc.account_id}
    finally:
        db.close()


def pay_latest_unpaid_tax(user_id: str) -> Dict[str, Any]:
    """直近の未納課税（assessed）を納付する。"""
    db = SessionLocal()
    try:
        assessment = db.execute(
            select(TaxAssessment)
            .where(TaxAssessment.user_id == user_id)
            .where(TaxAssessment.status == 'assessed')
            .order_by(TaxAssessment.assessment_id.desc())
            .limit(1)
        ).scalars().first()
        if not assessment:
            return {'success': False, 'message': '未納の課税がありません'}

        profile = db.execute(select(TaxProfile).where(TaxProfile.user_id == user_id)).scalars().first()
        if not profile or not profile.tax_account_id:
            return {'success': False, 'message': '納税口座が未設定です（?納税 設定 001-1234567）'}

        from_acc = db.execute(select(Account).where(Account.account_id == profile.tax_account_id)).scalars().first()
        if not from_acc:
            return {'success': False, 'message': '納税口座が見つかりません'}

        amount = _as_decimal(assessment.tax_amount)
        if amount <= 0:
            with db.begin():
                assessment.status = 'paid'
                assessment.paid_at = now_jst()
                db.add(assessment)
            return {'success': True, 'amount': '0'}

        from apps.banking.bank_service import transfer_funds

        try:
            tx = transfer_funds(
                from_account_number=from_acc.account_number,
                to_account_number=getattr(config, 'TAX_DEST_ACCOUNT_NUMBER', '1111111'),
                amount=amount,
                currency='JPY',
                description='所得税（手動納付）',
            )
        except Exception as e:
            return {'success': False, 'message': f'振込に失敗しました: {e}'}

        with db.begin():
            payment = TaxPayment(
                assessment_id=assessment.assessment_id,
                bank_transaction_id=tx.get('transaction_id') if isinstance(tx, dict) else None,
                amount=amount,
            )
            db.add(payment)
            assessment.status = 'paid'
            assessment.paid_at = now_jst()
            db.add(assessment)

            from apps.collections.collections_service import mark_case_resolved_if_exists
            mark_case_resolved_if_exists(db, case_type='tax', reference_id=assessment.assessment_id, note='manual_paid')

        return {'success': True, 'amount': str(amount), 'transaction_id': tx.get('transaction_id') if isinstance(tx, dict) else None}
    finally:
        db.close()
