"""共通: 口座選択FlexMessage。

税/借金で同じUIを使い回すための最小コンポーネント。
"""

from __future__ import annotations

from typing import List, Dict, Optional

from linebot.models import FlexSendMessage


def build_account_picker_flex(
    *,
    alt_text: str,
    title: str,
    description: str,
    accounts: List[Dict],
    account_postback_prefix: str,
    other_postback_data: str,
    cancel_postback_data: Optional[str] = None,
) -> FlexSendMessage:
    buttons = []

    for a in accounts:
        label = f"{a.get('branch_code', '???')}-{a.get('account_number', '')}"
        if a.get('balance') is not None:
            try:
                label = f"{label} 残高¥{int(float(a['balance'])):,}"
            except Exception:
                pass

        buttons.append(
            {
                "type": "button",
                "style": "primary",
                "action": {
                    "type": "postback",
                    "label": label[:20],
                    "data": f"{account_postback_prefix}&account_id={a['account_id']}",
                },
            }
        )

    buttons.append(
        {
            "type": "button",
            "style": "secondary",
            "action": {
                "type": "postback",
                "label": "その他の口座を登録",
                "data": other_postback_data,
            },
        }
    )

    if cancel_postback_data:
        buttons.append(
            {
                "type": "button",
                "style": "secondary",
                "action": {
                    "type": "postback",
                    "label": "キャンセル",
                    "data": cancel_postback_data,
                },
            }
        )

    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": description, "wrap": True, "size": "sm", "color": "#666666"},
                {"type": "separator", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons,
        },
    }

    return FlexSendMessage(alt_text=alt_text, contents=bubble)


def build_pin_prompt_flex(*, alt_text: str, title: str, note: str, cancel_postback_data: str) -> FlexSendMessage:
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": note, "wrap": True, "size": "sm", "color": "#666666", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {"type": "postback", "label": "キャンセル", "data": cancel_postback_data},
                }
            ],
        },
    }
    return FlexSendMessage(alt_text=alt_text, contents=bubble)
