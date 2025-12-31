from __future__ import annotations

from decimal import Decimal
from typing import Optional, List, Dict, Any

from linebot.models import FlexSendMessage


def _yen(v) -> str:
    try:
        return f"¥{int(Decimal(str(v))):,}"
    except Exception:
        return "-"


def _tax_status_ja(status: Any) -> str:
    s = str(status) if status is not None else ''
    mapping = {
        'assessed': '未納',
        'paid': '納付済み',
    }
    return mapping.get(s, s or '-')


def build_tax_dashboard_flex(
    *,
    tax_account_text: str,
    latest: Optional[Dict],
    income_total_so_far: Any = None,
    income_taxable_so_far: Any = None,
    estimated_tax: Any = None,
    period_end_text: str = '-',
) -> FlexSendMessage:
    status_lines = []
    if latest is None:
        status_lines = [
            {"type": "text", "text": "今週の課税はまだ確定していません", "wrap": True, "size": "sm", "color": "#666666"}
        ]
    else:
        status_lines = [
            {"type": "text", "text": f"税額: {_yen(latest.get('tax_amount'))}", "size": "sm"},
            {"type": "text", "text": f"状態: {_tax_status_ja(latest.get('status'))}", "size": "sm"},
            {"type": "text", "text": f"納付期限: {latest.get('due_text')}", "size": "sm"},
        ]

    income_lines = [
        {"type": "separator", "margin": "md"},
        {"type": "text", "text": "予想（現在まで）", "weight": "bold", "size": "md", "margin": "sm"},
        {"type": "text", "text": f"対象締め: {period_end_text}", "size": "xs", "color": "#666666"},
        {"type": "text", "text": f"所得合計: {_yen(income_total_so_far)}", "size": "sm"},
        {"type": "text", "text": f"課税対象: {_yen(income_taxable_so_far)}", "size": "sm"},
        {"type": "text", "text": f"予想税額: {_yen(estimated_tax)}", "size": "sm", "weight": "bold"},
    ]

    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "税ダッシュボード", "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"納税口座: {tax_account_text}", "wrap": True, "size": "sm", "color": "#666666", "margin": "sm"},
                {"type": "separator", "margin": "md"},
                *status_lines,
                *income_lines,
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "納税履歴", "data": "action=tax_history"}},
                {"type": "button", "style": "primary", "action": {"type": "postback", "label": "手動納税", "data": "action=tax_pay"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "口座を登録", "data": "action=tax_account_select"}},
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "納税ヘルプ", "data": "action=help_detail_tax"}},
            ],
        },
    }

    return FlexSendMessage(alt_text="税", contents=bubble)


def build_tax_help_flex() -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "納税ヘルプ", "weight": "bold", "size": "lg"},
                {"type": "text", "text": "・?税 でダッシュボード\n・口座登録→口座選択→暗証番号確認\n・手動納税は未納がある時のみ可能", "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "戻る", "data": "action=tax_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text="納税ヘルプ", contents=bubble)


def build_tax_history_flex(items: List[Dict]) -> FlexSendMessage:
    contents = [{"type": "text", "text": "納税履歴", "weight": "bold", "size": "lg"}]
    if not items:
        contents.append({"type": "text", "text": "履歴がありません", "size": "sm", "color": "#666666", "margin": "md"})
    else:
        contents.append({"type": "separator", "margin": "md"})
        for it in items[:8]:
            contents.extend(
                [
                    {"type": "text", "text": f"{it.get('period')}  {_yen(it.get('tax_amount'))}", "size": "sm"},
                    {"type": "text", "text": f"状態: {_tax_status_ja(it.get('status'))}", "size": "xs", "color": "#666666"},
                ]
            )

    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {"type": "box", "layout": "vertical", "contents": contents},
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "戻る", "data": "action=tax_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text="納税履歴", contents=bubble)


def build_tax_result_flex(title: str, message: str) -> FlexSendMessage:
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
                {"type": "button", "style": "secondary", "action": {"type": "postback", "label": "ダッシュボード", "data": "action=tax_dashboard"}},
            ],
        },
    }
    return FlexSendMessage(alt_text=title, contents=bubble)
