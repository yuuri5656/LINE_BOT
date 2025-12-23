from __future__ import annotations

import re
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select

from linebot.models import FlexSendMessage, TextSendMessage

import config
from apps.banking.main_bank_system import SessionLocal, Account, Branch
from apps.banking.api import banking_api
from apps.tax.models import TaxProfile, TaxAssessment
from apps.tax.tax_flex import (
    build_tax_dashboard_flex,
    build_tax_help_flex,
    build_tax_history_flex,
    build_tax_result_flex,
)
from apps.common.account_picker_flex import build_account_picker_flex, build_pin_prompt_flex
from apps.banking.bank_service import verify_pin_for_account
from apps.utilities.timezone_utils import now_jst


_BRANCH_ACCOUNT_RE = re.compile(r"^(?P<branch>\d{3})[- ](?P<acc>\d{7})$")
_PIN_RE = re.compile(r"^\d{4}$")


def _as_int(v: Any) -> Optional[int]:
    try:
        return int(str(v))
    except Exception:
        return None


def list_user_accounts(user_id: str) -> List[Dict[str, Any]]:
    # 口座選択UIは通帳と同じ見た目にするため、銀行APIの詳細口座情報を使う
    accounts = banking_api.get_accounts_by_user(user_id)
    return [a for a in accounts if a and a.get('account_id')]


def _current_tax_cycle_bounds(now: datetime) -> tuple[datetime, datetime]:
    """現在の課税サイクル（次の日曜15:01をendとする）[start, end) を返す。"""
    # now は tz-aware (JST) 前提
    days_until_sun = (6 - now.weekday()) % 7
    end_date = now.date() + timedelta(days=days_until_sun)
    end = datetime.combine(end_date, time(15, 1), tzinfo=now.tzinfo)
    if now >= end:
        end = end + timedelta(days=7)
    start = end - timedelta(days=7)
    return start, end


def _income_so_far(user_id: str) -> Dict[str, Any]:
    from apps.tax.models import TaxIncomeEvent
    from sqlalchemy import func

    now = now_jst()
    start, end = _current_tax_cycle_bounds(now)

    db = SessionLocal()
    try:
        totals = db.execute(
            select(
                func.coalesce(func.sum(TaxIncomeEvent.amount), 0),
                func.coalesce(func.sum(TaxIncomeEvent.taxable_amount), 0),
            )
            .where(TaxIncomeEvent.user_id == user_id)
            .where(TaxIncomeEvent.occurred_at >= start)
            .where(TaxIncomeEvent.occurred_at < now)
        ).first()

        total_income = Decimal(str(totals[0]))
        taxable_income = Decimal(str(totals[1]))

        from apps.tax.tax_service import compute_tax_amount

        _, est_tax = compute_tax_amount(taxable_income)

        try:
            end_text = end.strftime('%Y-%m-%d %H:%M')
        except Exception:
            end_text = str(end)

        return {
            'period_start': start,
            'period_end': end,
            'period_end_text': end_text,
            'income_total_so_far': total_income,
            'income_taxable_so_far': taxable_income,
            'estimated_tax': est_tax,
        }
    finally:
        db.close()


def _tax_account_text(user_id: str) -> str:
    db = SessionLocal()
    try:
        profile = db.execute(select(TaxProfile).where(TaxProfile.user_id == user_id)).scalars().first()
        if not profile or not profile.tax_account_id:
            return '未設定'

        row = db.execute(
            select(Account, Branch.code)
            .join(Branch, Account.branch_id == Branch.branch_id, isouter=True)
            .where(Account.account_id == profile.tax_account_id)
        ).first()
        if not row:
            return '未設定'

        acc, branch_code = row
        return f"{branch_code or '---'}-{acc.account_number}"
    finally:
        db.close()


def _latest_assessment_dict(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        a = db.execute(
            select(TaxAssessment).where(TaxAssessment.user_id == user_id).order_by(TaxAssessment.assessment_id.desc()).limit(1)
        ).scalars().first()
        if not a:
            return None

        due_text = ''
        if a.payment_window_end_at:
            try:
                due_text = a.payment_window_end_at.astimezone(a.payment_window_end_at.tzinfo).strftime('%Y-%m-%d')
            except Exception:
                due_text = str(a.payment_window_end_at)

        return {
            'tax_amount': a.tax_amount,
            'status': a.status,
            'due_text': due_text or '-',
        }
    finally:
        db.close()


def _history_items(user_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(TaxAssessment)
            .where(TaxAssessment.user_id == user_id)
            .order_by(TaxAssessment.assessment_id.desc())
            .limit(8)
        ).scalars().all()

        items: List[Dict[str, Any]] = []
        for a in rows:
            period = '-'
            try:
                if a.due_at:
                    period = a.due_at.astimezone(a.due_at.tzinfo).strftime('%Y-%m-%d')
            except Exception:
                pass

            items.append({'period': period, 'tax_amount': a.tax_amount, 'status': a.status})
        return items
    finally:
        db.close()


def build_dashboard(user_id: str) -> FlexSendMessage:
    sofar = _income_so_far(user_id)
    return build_tax_dashboard_flex(
        tax_account_text=_tax_account_text(user_id),
        latest=_latest_assessment_dict(user_id),
        income_total_so_far=sofar.get('income_total_so_far'),
        income_taxable_so_far=sofar.get('income_taxable_so_far'),
        estimated_tax=sofar.get('estimated_tax'),
        period_end_text=str(sofar.get('period_end_text') or '-'),
    )


def handle_tax_postback(*, action: str, parsed: Dict[str, str], user_id: str, sessions) -> Optional[Any]:
    if action == 'tax_dashboard':
        return build_dashboard(user_id)

    if action == 'tax_help':
        return build_tax_help_flex()

    if action == 'tax_history':
        return build_tax_history_flex(_history_items(user_id))

    if action == 'tax_pay':
        from apps.tax.tax_service import pay_latest_unpaid_tax

        res = pay_latest_unpaid_tax(user_id)
        if not res.get('success'):
            return build_tax_result_flex('手動納税', str(res.get('message', '失敗しました')))
        return build_tax_result_flex('手動納税', f"納付しました: ¥{int(Decimal(res.get('amount', '0'))):,}")

    if action == 'tax_account_select':
        accounts = list_user_accounts(user_id)
        if not accounts:
            return build_tax_result_flex('口座登録', '口座が見つかりません。先に ?口座開設 を実行してください。')

        return build_account_picker_flex(
            alt_text='口座選択',
            title='納税口座の選択',
            description='納税に使う口座を選んでください。',
            accounts=accounts,
            account_postback_prefix='action=tax_account_choose',
            other_postback_data='action=tax_account_other',
            cancel_postback_data='action=tax_dashboard',
        )

    if action == 'tax_account_other':
        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict):
            state = {}
        state['flex_flow'] = {
            'type': 'tax_set_account_manual',
            'step': 'await_branch_account',
            'started_at': now_jst().isoformat(),
        }
        sessions[user_id] = state
        return TextSendMessage(text='支店-口座番号を入力してください（例: 001-1234567）')

    if action == 'tax_account_choose':
        account_id = _as_int(parsed.get('account_id'))
        if not account_id:
            return build_tax_result_flex('口座登録', '口座が不正です')

        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict):
            state = {}
        state['flex_flow'] = {
            'type': 'tax_set_account',
            'step': 'await_pin',
            'account_id': int(account_id),
            'started_at': now_jst().isoformat(),
        }
        sessions[user_id] = state
        return build_pin_prompt_flex(
            alt_text='暗証番号',
            title='暗証番号確認',
            note='暗証番号(4桁)を入力してください。',
            cancel_postback_data='action=tax_dashboard',
        )

    return None


def handle_tax_text_flow(*, text: str, user_id: str, sessions) -> Optional[Any]:
    state = sessions.get(user_id) if sessions else None
    if not isinstance(state, dict):
        return None

    flow = state.get('flex_flow')
    if not isinstance(flow, dict):
        return None

    if flow.get('type') == 'tax_set_account_manual' and flow.get('step') == 'await_branch_account':
        m = _BRANCH_ACCOUNT_RE.match(text.strip())
        if not m:
            return TextSendMessage(text='形式が違います。例: 001-1234567')

        branch_code = m.group('branch')
        account_number = m.group('acc')

        # 口座が本人名義か確認し、account_idに変換
        db = SessionLocal()
        try:
            br = db.execute(select(Branch).where(Branch.code == branch_code)).scalars().first()
            if not br:
                return TextSendMessage(text='支店が見つかりません')

            acc = db.execute(
                select(Account)
                .where(Account.branch_id == br.branch_id)
                .where(Account.account_number == account_number)
                .where(Account.user_id == user_id)
            ).scalars().first()
            if not acc:
                return TextSendMessage(text='口座が見つかりません（あなた名義のみ設定可能）')

            flow2 = dict(flow)
            flow2['type'] = 'tax_set_account'
            flow2['step'] = 'await_pin'
            flow2['account_id'] = int(acc.account_id)
            state['flex_flow'] = flow2
            sessions[user_id] = state

            return build_pin_prompt_flex(
                alt_text='暗証番号',
                title='暗証番号確認',
                note='暗証番号(4桁)を入力してください。',
                cancel_postback_data='action=tax_dashboard',
            )
        finally:
            db.close()

    if flow.get('type') == 'tax_set_account' and flow.get('step') == 'await_pin':
        pin = text.strip()
        if not _PIN_RE.match(pin):
            return TextSendMessage(text='暗証番号は4桁で入力してください')

        account_id = _as_int(flow.get('account_id'))
        if not account_id:
            return TextSendMessage(text='口座が不正です')

        if not verify_pin_for_account(int(account_id), pin):
            return TextSendMessage(text='暗証番号が違います')

        from apps.tax.tax_service import set_tax_account_by_id

        res = set_tax_account_by_id(user_id, int(account_id))

        # 完了したらフローを消す
        state.pop('flex_flow', None)
        sessions[user_id] = state

        if not res.get('success'):
            return build_tax_result_flex('口座登録', str(res.get('message', '失敗しました')))

        return build_tax_result_flex('口座登録', '納税口座を登録しました')

    return None
