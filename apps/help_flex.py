def get_account_flex_bubble(account_info):
    # 口座情報をFlexMessageバブル形式で返す
    # 作成日を「YYYY年MM月DD日」に整形
    created_at = account_info.get('created_at')
    if created_at:
        try:
            if hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime('%Y年%m月%d日')
            else:
                # 例: '2025-11-18...' → '2025年11月18日'
                s = str(created_at)[:10]
                y, m, d = s.split('-')
                created_at_str = f'{y}年{m}月{d}日'
        except Exception:
            created_at_str = str(created_at)
    else:
        created_at_str = ''

    # 状態を日本語化
    status_map = {'active': '利用可能', 'inactive': '利用不可', 'closed': '解約済み'}
    status_jp = status_map.get(str(account_info.get('status')), str(account_info.get('status')))

    # 種別を日本語化
    type_map = {'ordinary': '普通', 'current': '当座', 'time': '定期'}
    type_jp = type_map.get(str(account_info.get('type')), str(account_info.get('type')))

    # モダンで機能的なカードレイアウト（絵文字なし）
    # 左側にラベル、右側に値を揃える二列レイアウト。
    # 色味は控えめにし、余白とタイポグラフィで見やすさを確保。
    balance_val = account_info.get('balance') or ''
    currency = account_info.get('currency') or ''

    # 値が数値文字列ならカンマ区切りに整形（簡易）
    try:
        # balance が既にフォーマット済みの文字列の可能性もある
        if isinstance(balance_val, (int, float)):
            balance_display = f"{balance_val:,.2f}"
        else:
            # 数字文字列なら浮動小数点として整形
            b = float(str(balance_val))
            balance_display = f"{b:,.2f}"
    except Exception:
        balance_display = str(balance_val)

    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "18px",
            "backgroundColor": "#FAFBFD",
            "cornerRadius": "12px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "口座情報", "weight": "bold", "size": "lg", "color": "#111317"},
                        {"type": "text", "text": account_info.get('branch_name') or '', "size": "sm", "color": "#6B7280", "align": "end"}
                    ],
                    "spacing": "md"
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
                                {"type": "text", "text": "氏名", "size": "sm", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": account_info.get('full_name') or '（未登録）', "size": "sm", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "支店", "size": "xs", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": f"{account_info.get('branch_name') or ''} ({account_info.get('branch_code') or ''})", "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "口座番号", "size": "sm", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": account_info.get('account_number') or '—', "size": "sm", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "種別", "size": "xs", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": type_jp, "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "状態", "size": "xs", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": status_jp, "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "作成日", "size": "xs", "color": "#6B7280", "flex": 2},
                                {"type": "text", "text": created_at_str or '—', "size": "xs", "color": "#111317", "align": "end", "flex": 5}
                            ],
                            "spacing": "sm",
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "残高", "size": "sm", "color": "#6B7280"},
                        {"type": "text", "text": f"{balance_display} {currency}", "size": "md", "color": "#0F172A", "align": "end", "weight": "bold"}
                    ]
                }
            ]
        }
    }
    return bubble
from linebot.models import FlexSendMessage

def get_help_flex():
    help_carousel = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "口座関連", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#1E90FF",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?口座開設", "weight": "bold", "size": "md", "color": "#1E90FF", "margin": "md"},
                        {"type": "text", "text": "新しい口座を開設します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?口座情報", "weight": "bold", "size": "md", "color": "#1E90FF", "margin": "md"},
                        {"type": "text", "text": "あなたの口座情報を表示します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?通帳", "weight": "bold", "size": "md", "color": "#1E90FF", "margin": "md"},
                        {"type": "text", "text": "最近の取引履歴（最新20件）を表示します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 1/3", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "口座関連の詳細ヘルプ",
                                "data": "help_detail_account"
                            },
                            "style": "primary",
                            "color": "#1E90FF",
                            "margin": "md"
                        }
                    ],
                    "paddingAll": "10px"
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ミニゲーム口座", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#FF6347",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?ミニゲーム口座登録", "weight": "bold", "size": "md", "color": "#FF6347", "margin": "md"},
                        {"type": "text", "text": "お持ちの口座をミニゲーム専用口座として登録します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "登録手順:", "weight": "bold", "size": "sm", "margin": "md"},
                        {"type": "text", "text": "1. 支店番号（3桁）\n2. 口座番号（7桁）\n3. フルネーム（カタカナ）\n4. 暗証番号（4桁）", "size": "xs", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "※キャンセルは「?キャンセル」と入力", "size": "xs", "color": "#999999", "wrap": True, "margin": "md"}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 2/3", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "ミニゲーム口座の詳細ヘルプ",
                                "data": "help_detail_minigame"
                            },
                            "style": "primary",
                            "color": "#FF6347",
                            "margin": "md"
                        }
                    ],
                    "paddingAll": "10px"
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "じゃんけんゲーム", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#32CD32",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?じゃんけん", "weight": "bold", "size": "md", "color": "#32CD32", "margin": "md"},
                        {"type": "text", "text": "じゃんけんゲームを開始します（グループのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?参加", "weight": "bold", "size": "md", "color": "#32CD32", "margin": "md"},
                        {"type": "text", "text": "募集中のゲームに参加します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?開始", "weight": "bold", "size": "md", "color": "#32CD32", "margin": "md"},
                        {"type": "text", "text": "ゲームを開始します（ホストのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?キャンセル", "weight": "bold", "size": "md", "color": "#32CD32", "margin": "md"},
                        {"type": "text", "text": "参加をキャンセルします", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 3/3", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "じゃんけんゲームの詳細ヘルプ",
                                "data": "help_detail_janken"
                            },
                            "style": "primary",
                            "color": "#32CD32",
                            "margin": "md"
                        }
                    ],
                    "paddingAll": "10px"
                }
            }
        ]
    }
    return FlexSendMessage(alt_text="コマンドヘルプ", contents=help_carousel)

def get_detail_account_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🏦 口座関連 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1E90FF"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#1E90FF"},
                {
                    "type": "text",
                    "text": "?口座開設",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#1E90FF",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "新規口座を作成します。必要情報を順番に入力してください。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#1E90FF", "margin": "md"},
                {
                    "type": "text",
                    "text": "?口座情報",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#1E90FF",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "登録済み口座の詳細（番号・残高・支店名など）を表示します。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#1E90FF", "margin": "md"},
                {
                    "type": "text",
                    "text": "?通帳",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#1E90FF",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "直近20件の取引履歴を表示します。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#F0F8FF"
        }
    }
    return FlexSendMessage(alt_text="口座関連詳細ヘルプ", contents=detail)

def get_detail_minigame_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎮 ミニゲーム口座 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FF6347"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#FF6347"},
                {
                    "type": "text",
                    "text": "?ミニゲーム口座登録",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FF6347",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "口座をミニゲーム専用として登録。支店番号・口座番号・カタカナ氏名・暗証番号を順に入力。登録後はミニゲームで利用可能。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#FF6347", "margin": "md"},
                {
                    "type": "text",
                    "text": "キャンセルは「?キャンセル」で中断できます。",
                    "size": "md",
                    "color": "#FF6347",
                    "wrap": True,
                    "margin": "md"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#FFF5F0"
        }
    }
    return FlexSendMessage(alt_text="ミニゲーム口座詳細ヘルプ", contents=detail)

def get_detail_janken_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "✊ じゃんけんゲーム 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#32CD32"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#32CD32"},
                {
                    "type": "text",
                    "text": "?じゃんけん",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#32CD32",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "グループでゲームを開始。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#32CD32", "margin": "md"},
                {
                    "type": "text",
                    "text": "?参加",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#32CD32",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "募集中のゲームに参加。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#32CD32", "margin": "md"},
                {
                    "type": "text",
                    "text": "?開始",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#32CD32",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "ホストがゲームを開始。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#32CD32", "margin": "md"},
                {
                    "type": "text",
                    "text": "?キャンセル",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#32CD32",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "参加を取り消し。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#32CD32", "margin": "md"},
                {
                    "type": "text",
                    "text": "手（グー/チョキ/パー）を個別チャットで送信して勝負。",
                    "size": "md",
                    "color": "#32CD32",
                    "wrap": True,
                    "margin": "md"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#F0FFF0"
        }
    }
    return FlexSendMessage(alt_text="じゃんけんゲーム詳細ヘルプ", contents=detail)
