from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import select

import config
from linebot.models import FlexSendMessage, TextSendMessage

from apps.banking.main_bank_system import SessionLocal, Account, Branch
from apps.common.account_picker_flex import build_account_picker_flex, build_pin_prompt_flex
from apps.banking.bank_service import verify_pin_for_account
from apps.loans.models import Loan
from apps.loans.loan_flex import (
    build_loan_dashboard_flex,
    build_loan_borrow_intro_flex,
    build_loan_help_flex,
    build_loan_prompt_flex,
    build_loan_contract_flex,
)
from apps.tax.tax_service import get_prev_week_total_income
from apps.collections.collections_service import is_blacklisted
from apps.loans.loan_service import can_borrow, create_loan, manual_repay
from apps.utilities.timezone_utils import now_jst


_PIN_RE = re.compile(r"^\d{4}$")
_AMOUNT_RE = re.compile(r"^\d{1,12}$")
_BRANCH_ACCOUNT_RE = re.compile(r"^(?P<branch>\d{3})[- ](?P<acc>\d{7})$")


def _as_int(v: Any) -> Optional[int]:
    try:
        return int(str(v))
    except Exception:
        return None


def _yen(n: Any) -> str:
    try:
        return f"¥{int(Decimal(str(n))):,}"
    except Exception:
        return "-"


def _get_active_loan(user_id: str) -> Optional[Loan]:
    db = SessionLocal()
    try:
        return db.execute(
            select(Loan).where(Loan.user_id == user_id).where(Loan.status == 'active').order_by(Loan.loan_id.desc()).limit(1)
        ).scalars().first()
    finally:
        db.close()


def build_dashboard(user_id: str) -> FlexSendMessage:
    loan = _get_active_loan(user_id)
    bl = False
    try:
        bl = is_blacklisted(user_id)
    except Exception:
        bl = False

    loan_dict = None
    if loan:
        loan_dict = {
            'balance': loan.outstanding_balance,
            'autopay_amount': loan.autopay_amount,
        }

    return build_loan_dashboard_flex(loan=loan_dict, blacklisted=bl)


def _calc_max_borrow_text(user_id: str) -> str:
    try:
        income = get_prev_week_total_income(user_id)
    except Exception:
        return '不明（所得参照に失敗）'

    mult = Decimal(str(getattr(config, 'LOAN_MAX_MULTIPLIER', 5)))
    max_amount = Decimal(str(income)) * mult
    return _yen(max_amount)


def handle_loan_postback(*, action: str, parsed: Dict[str, str], user_id: str, sessions) -> Optional[Any]:
    if action == 'loan_dashboard':
        return build_dashboard(user_id)

    if action == 'loan_help':
        return build_loan_help_flex()

    if action == 'loan_settings':
        return build_loan_prompt_flex(title='設定', message='現在は設定項目はありません。', cancel_data='action=loan_dashboard')

    if action == 'loan_borrow':
        # 既に借金がある場合は簡素に案内
        loan = _get_active_loan(user_id)
        if loan:
            return build_loan_prompt_flex(title='借入', message='現在借金があるため、新規借入はできません。', cancel_data='action=loan_dashboard')

        # ブラックリストは借入不可
        try:
            if is_blacklisted(user_id):
                return build_loan_prompt_flex(title='借入', message='ブラックリストのため借入できません。', cancel_data='action=loan_dashboard')
        except Exception:
            return build_loan_prompt_flex(title='借入', message='信用情報を参照できないため借入できません（DB権限を確認してください）。', cancel_data='action=loan_dashboard')

        return build_loan_borrow_intro_flex(max_amount_text=_calc_max_borrow_text(user_id))

    if action == 'loan_apply_start':
        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict):
            state = {}
        state['flex_flow'] = {
            'type': 'loan_apply',
            'step': 'await_principal',
            'started_at': now_jst().isoformat(),
        }
        sessions[user_id] = state
        return build_loan_prompt_flex(title='借入申請', message='借入額を入力してください（例: 50000）', cancel_data='action=loan_dashboard')

    if action == 'loan_account_choose':
        account_id = _as_int(parsed.get('account_id'))
        if not account_id:
            return build_loan_prompt_flex(title='借入申請', message='口座が不正です', cancel_data='action=loan_dashboard')

        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict) or not isinstance(state.get('flex_flow'), dict):
            return build_loan_prompt_flex(title='借入申請', message='申請情報が見つかりません。最初からやり直してください。', cancel_data='action=loan_dashboard')

        flow = state['flex_flow']
        flow['account_id'] = int(account_id)
        flow['step'] = 'await_pin'
        state['flex_flow'] = flow
        sessions[user_id] = state

        return build_pin_prompt_flex(
            alt_text='暗証番号',
            title='暗証番号確認',
            note='暗証番号(4桁)を入力してください。',
            cancel_postback_data='action=loan_dashboard',
        )

    if action == 'loan_account_other':
        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict):
            state = {}
        state['flex_flow'] = {
            'type': 'loan_apply',
            'step': 'await_branch_account',
            'started_at': now_jst().isoformat(),
        }
        sessions[user_id] = state
        return TextSendMessage(text='支店-口座番号を入力してください（例: 001-1234567）')

    if action == 'loan_contract_confirm':
        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict) or not isinstance(state.get('flex_flow'), dict):
            return build_loan_prompt_flex(title='契約', message='申請情報が見つかりません。最初からやり直してください。', cancel_data='action=loan_dashboard')

        flow = state['flex_flow']
        principal = flow.get('principal')
        daily_autopay = flow.get('daily_autopay')
        account_id = flow.get('account_id')

        if principal is None or daily_autopay is None or account_id is None:
            return build_loan_prompt_flex(title='契約', message='申請情報が不足しています。最初からやり直してください。', cancel_data='action=loan_dashboard')

        res = create_loan(
            user_id=user_id,
            principal=principal,
            receive_account_id=int(account_id),
            autopay_account_id=int(account_id),
            autopay_amount=daily_autopay,
        )

        state.pop('flex_flow', None)
        sessions[user_id] = state

        if not res.get('success'):
            return build_loan_prompt_flex(title='契約', message=str(res.get('message', '失敗しました')), cancel_data='action=loan_dashboard')

        return build_loan_prompt_flex(
            title='契約完了',
            message=f"借入しました: {_yen(res.get('principal'))}",
            cancel_data='action=loan_dashboard',
        )

    if action == 'loan_repay':
        state = sessions.get(user_id) if sessions else None
        if not isinstance(state, dict):
            state = {}
        state['flex_flow'] = {
            'type': 'loan_repay',
            'step': 'await_amount',
            'started_at': now_jst().isoformat(),
        }
        sessions[user_id] = state
        return build_loan_prompt_flex(title='返済', message='返済額を入力してください（1000円単位）', cancel_data='action=loan_dashboard')

    return None


def handle_loan_text_flow(*, text: str, user_id: str, sessions) -> Optional[Any]:
    state = sessions.get(user_id) if sessions else None
    if not isinstance(state, dict):
        return None

    flow = state.get('flex_flow')
    if not isinstance(flow, dict):
        return None

    if flow.get('type') == 'loan_repay' and flow.get('step') == 'await_amount':
        t = text.strip()
        if not _AMOUNT_RE.match(t):
            return TextSendMessage(text='数字で入力してください')

        amount = int(t)
        res = manual_repay(user_id, amount)
        state.pop('flex_flow', None)
        sessions[user_id] = state

        if not res.get('success'):
            return build_loan_prompt_flex(title='返済', message=str(res.get('message', '失敗しました')), cancel_data='action=loan_dashboard')
        return build_loan_prompt_flex(
            title='返済',
            message=f"返済しました: {_yen(res.get('paid'))}\n残高: {_yen(res.get('remaining_balance'))}",
            cancel_data='action=loan_dashboard',
        )

    if flow.get('type') == 'loan_apply' and flow.get('step') == 'await_branch_account':
        m = _BRANCH_ACCOUNT_RE.match(text.strip())
        if not m:
            return TextSendMessage(text='形式が違います。例: 001-1234567')

        branch_code = m.group('branch')
        account_number = m.group('acc')

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
                return TextSendMessage(text='口座が見つかりません（あなた名義のみ選択可能）')

            flow['account_id'] = int(acc.account_id)
            flow['step'] = 'await_pin'
            state['flex_flow'] = flow
            sessions[user_id] = state

            return build_pin_prompt_flex(
                alt_text='暗証番号',
                title='暗証番号確認',
                note='暗証番号(4桁)を入力してください。',
                cancel_postback_data='action=loan_dashboard',
            )
        finally:
            db.close()

    if flow.get('type') == 'loan_apply' and flow.get('step') == 'await_principal':
        t = text.strip()
        if not _AMOUNT_RE.match(t):
            return TextSendMessage(text='借入額は数字で入力してください')

        principal = int(t)
        ok, msg, meta = can_borrow(user_id, Decimal(str(principal)))
        if not ok:
            return TextSendMessage(text=str(msg))

        min_daily = int(Decimal(str(getattr(config, 'LOAN_MIN_AUTOPAY_DAILY', 1000))))
        min_monthly = min_daily * 30

        flow['principal'] = principal
        flow['step'] = 'await_monthly'
        flow['min_monthly'] = min_monthly
        flow['applied_rate'] = meta.get('applied_rate')
        state['flex_flow'] = flow
        sessions[user_id] = state

        return build_loan_prompt_flex(
            title='借入申請',
            message=f"最低月返済額: {_yen(min_monthly)}\n月返済額を入力してください（1000円単位）",
            cancel_data='action=loan_dashboard',
        )

    if flow.get('type') == 'loan_apply' and flow.get('step') == 'await_monthly':
        t = text.strip()
        if not _AMOUNT_RE.match(t):
            return TextSendMessage(text='月返済額は数字で入力してください')

        monthly = int(t)
        if monthly % 1000 != 0:
            return TextSendMessage(text='1000円単位で入力してください')

        min_monthly = int(flow.get('min_monthly') or 0)
        if monthly < min_monthly:
            return TextSendMessage(text=f"最低月返済額は {_yen(min_monthly)} です")

        # 内部は日次引落なので、月額を30日で割って1000円単位に丸める
        daily = int((monthly / 30) // 1000) * 1000
        if daily < int(Decimal(str(getattr(config, 'LOAN_MIN_AUTOPAY_DAILY', 1000)))):
            daily = int(Decimal(str(getattr(config, 'LOAN_MIN_AUTOPAY_DAILY', 1000))))

        flow['monthly_repay'] = monthly
        flow['daily_autopay'] = daily
        flow['step'] = 'await_account'
        state['flex_flow'] = flow
        sessions[user_id] = state

        # 口座選択Flex
        db = SessionLocal()
        try:
            rows = db.execute(
                select(Account, Branch.code)
                .join(Branch, Account.branch_id == Branch.branch_id, isouter=True)
                .where(Account.user_id == user_id)
                .where(Account.status.in_(['active', 'frozen']))
                .order_by(Account.account_id.asc())
            ).all()

            accounts = []
            for acc, branch_code in rows:
                accounts.append(
                    {
                        'account_id': int(acc.account_id),
                        'account_number': str(acc.account_number),
                        'branch_code': str(branch_code) if branch_code else '---',
                        'balance': acc.balance,
                    }
                )
        finally:
            db.close()

        if not accounts:
            return TextSendMessage(text='口座が見つかりません。先に ?口座開設 を実行してください。')

        return build_account_picker_flex(
            alt_text='口座選択',
            title='受取/返済口座',
            description='借入の受取と自動引落に使う口座を選んでください。',
            accounts=accounts,
            account_postback_prefix='action=loan_account_choose',
            other_postback_data='action=loan_account_other',
            cancel_postback_data='action=loan_dashboard',
        )

    if flow.get('type') == 'loan_apply' and flow.get('step') == 'await_pin':
        pin = text.strip()
        if not _PIN_RE.match(pin):
            return TextSendMessage(text='暗証番号は4桁で入力してください')

        account_id = _as_int(flow.get('account_id'))
        if not account_id:
            return TextSendMessage(text='口座が不正です')

        if not verify_pin_for_account(int(account_id), pin):
            return TextSendMessage(text='暗証番号が違います')

        # 契約内容を表示
        principal = flow.get('principal')
        monthly = flow.get('monthly_repay')
        daily = flow.get('daily_autopay')
        rate = flow.get('applied_rate')

        summary = (
            f"借入額: {_yen(principal)}\n"
            f"月返済額: {_yen(monthly)}（内部: 毎日{_yen(daily)}を自動引落）\n"
            f"利率(週): {rate or '-'}\n"
            f"注意: 返済が滞るとブラックリスト/差押えになります。"
        )

        flow['step'] = 'contract_ready'
        state['flex_flow'] = flow
        sessions[user_id] = state

        return build_loan_contract_flex(summary=summary)

    return None
