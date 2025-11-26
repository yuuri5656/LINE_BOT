"""
振り込み機能用FlexMessageテンプレート
"""
from linebot.models import FlexSendMessage


def get_transfer_guide_flex():
    """振り込み案内FlexMessage"""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💸 振り込み",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#1E90FF",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "振り込み手続きを開始します",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#111317",
                    "margin": "md"
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "手順:",
                            "weight": "bold",
                            "size": "md",
                            "color": "#1E90FF"
                        },
                        {
                            "type": "text",
                            "text": "1️⃣ 振込先の支店コード（3桁）",
                            "size": "sm",
                            "color": "#333333",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": "2️⃣ 振込先の口座番号（7桁）",
                            "size": "sm",
                            "color": "#333333",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "3️⃣ 振込金額",
                            "size": "sm",
                            "color": "#333333",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "4️⃣ 暗証番号（4桁）",
                            "size": "sm",
                            "color": "#333333",
                            "margin": "xs"
                        }
                    ],
                    "backgroundColor": "#F0F8FF",
                    "cornerRadius": "8px",
                    "paddingAll": "12px"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⚠️ ご注意",
                            "weight": "bold",
                            "size": "sm",
                            "color": "#FF6347"
                        },
                        {
                            "type": "text",
                            "text": "• 個別チャットでのみご利用可能です",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": "• キャンセルは「?キャンセル」と入力",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "まず、振込先の支店コード（3桁）を入力してください",
                    "size": "sm",
                    "color": "#1E90FF",
                    "align": "center",
                    "weight": "bold",
                    "wrap": True
                }
            ],
            "paddingAll": "12px"
        }
    }
    return FlexSendMessage(alt_text="振り込み案内", contents=bubble)


def get_transfer_success_flex(transfer_info: dict):
    """振り込み完了FlexMessage

    Args:
        transfer_info: {
            'from_account_number': str,
            'from_branch_code': str,
            'to_account_number': str,
            'to_branch_code': str,
            'amount': str,
            'currency': str,
            'executed_at': str (YYYY/MM/DD HH:MM),
            'new_balance': str
        }
    """
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "✅ 振り込み完了",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#32CD32",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "振り込みが完了しました",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#111317",
                    "margin": "md"
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "backgroundColor": "#FFFFFF",
                    "cornerRadius": "8px",
                    "paddingAll": "12px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "振込元", "size": "sm", "color": "#6B7280", "flex": 3},
                                {"type": "text", "text": f"{transfer_info.get('from_branch_code')}-{transfer_info.get('from_account_number')}",
                                 "size": "sm", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "振込先", "size": "sm", "color": "#6B7280", "flex": 3},
                                {"type": "text", "text": f"{transfer_info.get('to_branch_code')}-{transfer_info.get('to_account_number')}",
                                 "size": "sm", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "振込金額", "size": "sm", "color": "#6B7280", "flex": 3},
                                {"type": "text", "text": f"{transfer_info.get('amount')} {transfer_info.get('currency')}",
                                 "size": "md", "color": "#FF6347", "align": "end", "flex": 5, "weight": "bold"}
                            ],
                            "spacing": "sm",
                            "margin": "sm"
                        },
                        {"type": "separator", "margin": "md"},
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "実行日時", "size": "xs", "color": "#6B7280", "flex": 3},
                                {"type": "text", "text": transfer_info.get('executed_at', ''),
                                 "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "振込後残高", "size": "xs", "color": "#6B7280", "flex": 3},
                                {"type": "text", "text": f"{transfer_info.get('new_balance')} {transfer_info.get('currency')}",
                                 "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "取引が完了しました",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center"
                }
            ],
            "paddingAll": "12px"
        }
    }
    return FlexSendMessage(alt_text="振り込み完了", contents=bubble)


def get_transfer_error_flex(error_message: str, error_type: str = "error"):
    """振り込みエラーFlexMessage

    Args:
        error_message: エラーメッセージ
        error_type: エラー種別 ('error', 'validation', 'auth')
    """
    # エラー種別による色とアイコンの設定
    colors = {
        'error': {'bg': '#FF6347', 'icon': '❌'},
        'validation': {'bg': '#FFA500', 'icon': '⚠️'},
        'auth': {'bg': '#FF4500', 'icon': '🔒'}
    }

    config = colors.get(error_type, colors['error'])

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{config['icon']} 振り込みエラー",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": config['bg'],
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "振り込みを完了できませんでした",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#111317",
                    "margin": "md"
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "backgroundColor": "#FFF5F5",
                    "cornerRadius": "8px",
                    "paddingAll": "12px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "エラー内容:",
                            "weight": "bold",
                            "size": "sm",
                            "color": config['bg']
                        },
                        {
                            "type": "text",
                            "text": error_message,
                            "size": "sm",
                            "color": "#333333",
                            "wrap": True,
                            "margin": "sm"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💡 対処方法",
                            "weight": "bold",
                            "size": "sm",
                            "color": "#1E90FF"
                        },
                        {
                            "type": "text",
                            "text": "• 入力内容を確認してください\n• 残高が不足していないか確認してください\n• 振込先の口座情報が正しいか確認してください",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "「?振り込み」で再度お試しください",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center"
                }
            ],
            "paddingAll": "12px"
        }
    }
    return FlexSendMessage(alt_text="振り込みエラー", contents=bubble)


def get_account_selection_flex(accounts: list):
    """口座選択用FlexMessage（複数口座がある場合）

    Args:
        accounts: 口座情報のリスト
    """
    from apps.help_flex import get_account_flex_bubble

    bubbles = []
    for acc in accounts:
        bubble = get_account_flex_bubble(acc)

        # 振り込み用のボタンを追加
        footer = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "この口座から振り込む",
                        "data": f"action=select_transfer_account&branch_code={acc.get('branch_code')}&account_number={acc.get('account_number')}"
                    },
                    "style": "primary",
                    "color": "#1E90FF"
                }
            ],
            "paddingAll": "12px"
        }
        bubble["footer"] = footer
        bubbles.append(bubble)

    carousel = {
        "type": "carousel",
        "contents": bubbles
    }

    return FlexSendMessage(alt_text="振込口座を選択してください", contents=carousel)
