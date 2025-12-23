from __future__ import annotations

from decimal import Decimal
from typing import Optional, Dict

from linebot.models import FlexSendMessage


def _yen(v) -> str:
    try:
        return f"¥{int(Decimal(str(v))):,}"
    except Exception:
        return "-"


def build_loan_dashboard_flex(*, loan: Optional[Dict], blacklisted: bool) -> FlexSendMessage:
    body = [{"type": "text", "text": "借金ダッシュボード", "weight": "bold", "size": "lg"}]

    if blacklisted:
        body.append({"type": "text", "text": "状態: ブラックリスト", "size": "sm", "color": "#666666", "margin": "md"})

    if not loan:
        body.append({"type": "text", "text": "現在の借金はありません", "size": "sm", "color": "#666666", "margin": "md"})
    else:
        body.extend(
            [
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"残高: {_yen(loan.get('balance'))}", "size": "sm"},
                {"type": "text", "text": f"返済額(毎日): {_yen(loan.get('autopay_amount'))}", "size": "sm"},
            ]
        )

    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {"type": "box", "layout": "vertical", "contents": body},
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "借りる", "data": "action=loan_borrow"}},
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "返す", "data": "action=loan_repay"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "設定", "data": "action=loan_settings"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "ヘルプ", "data": "action=loan_help"}},
            ],
        },
    }

    return FlexSendMessage(alt_text="借金", contents=bubble)


def build_loan_borrow_intro_flex(*, max_amount_text: str) -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "借入申請", "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"借入上限: {max_amount_text}", "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
                {"type": "text", "text": "注意: 返済が滞るとブラックリスト/差押えになります。", "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "申請する", "data": "action=loan_apply_start"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "キャンセル", "data": "action=loan_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text="借入申請", contents=bubble)


def build_loan_prompt_flex(*, title: str, message: str, cancel_data: str) -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": message, "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "キャンセル", "data": cancel_data}},
            ],
        },
    }
    return FlexSendMessage(alt_text=title, contents=bubble)


def build_loan_contract_flex(*, summary: str) -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "契約内容の確認", "weight": "bold", "size": "lg"},
                {"type": "text", "text": summary, "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "契約する", "data": "action=loan_contract_confirm"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "キャンセル", "data": "action=loan_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text="契約", contents=bubble)


def build_loan_help_flex() -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "借金ヘルプ", "weight": "bold", "size": "lg"},
                {"type": "text", "text": "・?借金 でダッシュボード\n・借りる→申請→金額→月返済額→口座選択→契約\n・月返済額は内部で毎日の自動引落額に換算されます\n・返済が滞るとブラックリスト/差押え", "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "戻る", "data": "action=loan_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text="借金ヘルプ", contents=bubble)
