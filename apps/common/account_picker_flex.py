"""共通: 口座選択FlexMessage（カルーセル）。

税/借金で同じUIを使い回す。
通帳の口座選択UI（口座1つ=1バブル）と揃える。
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
    from apps.help_flex import get_account_flex_bubble

    bubbles = []

    # 先頭に説明バブル（1つだけ）
    intro_footer_buttons = [
        {
            "type": "button",
            "action": {"type": "postback", "label": "その他の口座を登録", "data": other_postback_data},
            "style": "secondary",
            "margin": "md",
        }
    ]
    if cancel_postback_data:
        intro_footer_buttons.append(
            {
                "type": "button",
                "action": {"type": "postback", "label": "キャンセル", "data": cancel_postback_data},
                "style": "secondary",
                "margin": "sm",
            }
        )

    intro = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [{"type": "text", "text": title, "weight": "bold", "size": "xl", "color": "#ffffff"}],
            "backgroundColor": "#1E90FF",
            "paddingAll": "20px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": description, "wrap": True, "size": "sm", "color": "#666666"}
            ],
            "paddingAll": "20px",
        },
        "footer": {"type": "box", "layout": "vertical", "contents": intro_footer_buttons, "paddingAll": "12px"},
    }
    bubbles.append(intro)

    # 各口座を1バブルで表示（通帳/振込と同じカード）
    for a in accounts:
        bubble = get_account_flex_bubble(a)
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "この口座を選択",
                        "data": f"{account_postback_prefix}&account_id={a['account_id']}",
                    },
                    "style": "primary",
                    "color": "#1E90FF",
                }
            ],
            "paddingAll": "12px",
        }
        bubbles.append(bubble)

    return FlexSendMessage(alt_text=alt_text, contents={"type": "carousel", "contents": bubbles})


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
