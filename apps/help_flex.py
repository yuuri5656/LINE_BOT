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
                        {"type": "text", "text": "最近の取引履歴（最新20件）を表示します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?振り込み", "weight": "bold", "size": "md", "color": "#1E90FF", "margin": "md"},
                        {"type": "text", "text": "他の口座へ振り込みを行います（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 1/4", "size": "xs", "color": "#999999", "align": "center"},
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
                        {"type": "text", "text": "ページ 2/4", "size": "xs", "color": "#999999", "align": "center"},
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
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ショップ機能", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#FF8C00",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?ショップ", "weight": "bold", "size": "md", "color": "#FF8C00", "margin": "md"},
                        {"type": "text", "text": "ショップを開いて商品を購入できます", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?チップ残高", "weight": "bold", "size": "md", "color": "#FF8C00", "margin": "md"},
                        {"type": "text", "text": "現在のチップ残高を確認します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?チップ履歴", "weight": "bold", "size": "md", "color": "#FF8C00", "margin": "md"},
                        {"type": "text", "text": "チップの取引履歴を表示します（最新20件）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?チップ換金 [金額]", "weight": "bold", "size": "md", "color": "#FF8C00", "margin": "md"},
                        {"type": "text", "text": "チップを現金に換金します（個別チャットのみ）", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 3/4", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "ショップ機能の詳細ヘルプ",
                                "data": "help_detail_shop"
                            },
                            "style": "primary",
                            "color": "#FF8C00",
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
                        {"type": "text", "text": "株式システム", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#DC143C",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?株", "weight": "bold", "size": "md", "color": "#DC143C", "margin": "md"},
                        {"type": "text", "text": "株式ダッシュボードを表示します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "銘柄一覧", "weight": "bold", "size": "md", "color": "#DC143C", "margin": "md"},
                        {"type": "text", "text": "取引可能な銘柄の一覧を表示します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "銘柄詳細", "weight": "bold", "size": "md", "color": "#DC143C", "margin": "md"},
                        {"type": "text", "text": "銘柄の詳細情報とチャートを表示（チャート生成に時間がかかります）", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "保有株", "weight": "bold", "size": "md", "color": "#DC143C", "margin": "md"},
                        {"type": "text", "text": "あなたの保有株式を表示します", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 4/5", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "株式システムの詳細ヘルプ",
                                "data": "help_detail_stock"
                            },
                            "style": "primary",
                            "color": "#DC143C",
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
                        {"type": "text", "text": "ユーティリティ", "weight": "bold", "size": "xl", "color": "#ffffff"}
                    ],
                    "backgroundColor": "#9370DB",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "?userid", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "あなたのユーザーIDを表示します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?明日の時間割", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "明日の授業時間割を表示します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?おみくじ", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "運勢を占います", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?RPN [式]", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "逆ポーランド記法で計算します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?setname [名前]", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "表示名を設定します", "size": "sm", "color": "#666666", "wrap": True},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "?労働", "weight": "bold", "size": "md", "color": "#9370DB", "margin": "md"},
                        {"type": "text", "text": "15分に1回、800円～1800円の報酬を獲得します", "size": "sm", "color": "#666666", "wrap": True}
                    ],
                    "spacing": "sm",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 5/5", "size": "xs", "color": "#999999", "align": "center"},
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "ユーティリティの詳細ヘルプ",
                                "data": "help_detail_utility"
                            },
                            "style": "primary",
                            "color": "#9370DB",
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
                },
                {"type": "separator", "color": "#1E90FF", "margin": "md"},
                {
                    "type": "text",
                    "text": "?振り込み",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#1E90FF",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "他の口座へ振り込みを行います。支店コード、口座番号、金額、暗証番号を順に入力してください。",
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

def get_detail_shop_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🛒 ショップ機能 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FF8C00"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#FF8C00"},
                {
                    "type": "text",
                    "text": "?ショップ",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FF8C00",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "商品カテゴリを表示し、チップを使って商品を購入できます。商品購入にはチップ残高と支払い口座の登録が必要です。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#FF8C00", "margin": "md"},
                {
                    "type": "text",
                    "text": "?チップ残高",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FF8C00",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "現在保有しているチップの残高を確認できます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#FF8C00", "margin": "md"},
                {
                    "type": "text",
                    "text": "?チップ履歴",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FF8C00",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "最近のチップ取引履歴（最新20件）を表示します。購入や換金の履歴を確認できます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#FF8C00", "margin": "md"},
                {
                    "type": "text",
                    "text": "?チップ換金 [金額]",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FF8C00",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "保有チップを現金に換金します。個別チャットでのみ利用可能。換金額を指定してください。（例：?チップ換金 100）",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#FFF5E6"
        }
    }
    return FlexSendMessage(alt_text="ショップ機能詳細ヘルプ", contents=detail)

def get_detail_stock_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📈 株式システム 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#DC143C"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#DC143C"},
                {
                    "type": "text",
                    "text": "?株（ダッシュボード）",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#DC143C",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "株式ダッシュボードを表示します。初回は株式口座の登録フローが開始されます。登録には銀行口座が必要です。個別チャット（1:1）専用機能です。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#DC143C", "margin": "md"},
                {
                    "type": "text",
                    "text": "銘柄一覧",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#DC143C",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "取引可能な全銘柄の一覧をカルーセル形式で表示します。各銘柄の現在価格、前日比、変動率を確認できます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#DC143C", "margin": "md"},
                {
                    "type": "text",
                    "text": "銘柄詳細",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#DC143C",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "選択した銘柄の詳細情報を表示します。株価チャート（価格推移グラフ）も自動生成されますが、チャート生成には10～15秒程度かかる場合があります。詳細画面から「購入」または「売却」ボタンで取引を開始できます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#DC143C", "margin": "md"},
                {
                    "type": "text",
                    "text": "保有株",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#DC143C",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "現在保有している株式の一覧を表示します。銘柄ごとの株数、取得単価、現在価格、評価損益を確認できます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#DC143C", "margin": "md"},
                {
                    "type": "text",
                    "text": "購入・売却",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#DC143C",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "銘柄詳細画面から購入または売却を選択し、株数を入力して取引を実行します。購入には銀行口座の残高が必要です。売却時は保有株数の範囲内で指定してください。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#DC143C", "margin": "md"},
                {
                    "type": "text",
                    "text": "⚠️ 注意事項",
                    "weight": "bold",
                    "size": "md",
                    "color": "#FF4500",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "• 株式口座の登録には銀行口座が必要です\n• 個別チャット（1:1）専用機能です\n• チャート生成には時間がかかります\n• 株価は定期的に自動更新されます",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#FFF0F0"
        }
    }
    return FlexSendMessage(alt_text="株式システム詳細ヘルプ", contents=detail)

def get_detail_utility_flex():
    detail = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🔧 ユーティリティ 詳細ヘルプ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#9370DB"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "separator", "color": "#9370DB"},
                {
                    "type": "text",
                    "text": "?userid",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "あなたのLINE User IDを表示します。サポートや問い合わせ時に必要になることがあります。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#9370DB", "margin": "md"},
                {
                    "type": "text",
                    "text": "?明日の時間割",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "明日の授業スケジュールを表示します。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#9370DB", "margin": "md"},
                {
                    "type": "text",
                    "text": "?おみくじ",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "今日の運勢を占います。大吉から大凶まで結果が出ます。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#9370DB", "margin": "md"},
                {
                    "type": "text",
                    "text": "?RPN [式]",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "逆ポーランド記法（Reverse Polish Notation）で数式を計算します。（例：?RPN 3 4 +）",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#9370DB", "margin": "md"},
                {
                    "type": "text",
                    "text": "?setname [名前]",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "表示名を変更します。（例：?setname 太郎）",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                },
                {"type": "separator", "color": "#9370DB", "margin": "md"},
                {
                    "type": "text",
                    "text": "?労働",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#9370DB",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "会社で労働して報酬を得ます。15分に1回実行可能で、800円～1800円のランダムな報酬が給与振込口座に振り込まれます。初回は給与振込口座の登録が必要です。",
                    "size": "md",
                    "color": "#333333",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "spacing": "md",
            "paddingAll": "lg",
            "backgroundColor": "#F3E5F5"
        }
    }
    return FlexSendMessage(alt_text="ユーティリティ詳細ヘルプ", contents=detail)

def get_update_announcement_flex():
    """大型アップデート情報をFlexMessageで返す"""
    announcement = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🎉 大型アップデート",
                            "weight": "bold",
                            "size": "xxl",
                            "color": "#ffffff",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": "2025年12月 リリース",
                            "size": "sm",
                            "color": "#ffffff",
                            "align": "center",
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#FF6B6B",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "主要な新機能",
                            "weight": "bold",
                            "size": "xl",
                            "color": "#333333"
                        },
                        {"type": "separator", "margin": "lg", "color": "#FF6B6B"},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📈 株式システム",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#DC143C",
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "• リアルタイム株価更新\n• チャート表示機能\n• 保有株式管理",
                                    "size": "sm",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "💼 労働システム",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#9370DB",
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "• 15分ごとに労働可能\n• 給与自動振込\n• 800～1800円の報酬",
                                    "size": "sm",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ]
                        }
                    ],
                    "spacing": "md",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 1/2", "size": "xs", "color": "#999999", "align": "center"}
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
                        {
                            "type": "text",
                            "text": "✨ システム改善",
                            "weight": "bold",
                            "size": "xxl",
                            "color": "#ffffff",
                            "align": "center"
                        }
                    ],
                    "backgroundColor": "#4ECDC4",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "改善内容",
                            "weight": "bold",
                            "size": "xl",
                            "color": "#333333"
                        },
                        {"type": "separator", "margin": "lg", "color": "#4ECDC4"},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎨 UI/UX改善",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#1E90FF",
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "• Flex Messageの全面刷新\n• 視覚的で分かりやすいデザイン\n• ボタン操作の追加",
                                    "size": "sm",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "⏰ 日時処理の統一",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#32CD32",
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "• 全システムで日本時間(JST)に統一\n• 表示形式の統一化",
                                    "size": "sm",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🐛 バグ修正",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#FF8C00",
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "• セッション管理の改善\n• エラーハンドリングの強化\n• その他多数のバグ修正",
                                    "size": "sm",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ]
                        }
                    ],
                    "spacing": "md",
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "ページ 2/2", "size": "xs", "color": "#999999", "align": "center"},
                        {"type": "separator", "margin": "md"},
                        {
                            "type": "text",
                            "text": "💡 詳細は各ヘルプをご確認ください",
                            "size": "sm",
                            "color": "#333333",
                            "align": "center",
                            "margin": "md",
                            "wrap": True,
                            "weight": "bold"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "?ヘルプ - 全機能",
                                        "text": "?ヘルプ"
                                    },
                                    "style": "primary",
                                    "color": "#1E90FF",
                                    "margin": "md"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "postback",
                                        "label": "株式システムの詳細",
                                        "data": "help_detail_stock"
                                    },
                                    "style": "primary",
                                    "color": "#DC143C",
                                    "margin": "sm"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "postback",
                                        "label": "ユーティリティの詳細",
                                        "data": "help_detail_utility"
                                    },
                                    "style": "primary",
                                    "color": "#9370DB",
                                    "margin": "sm"
                                }
                            ]
                        }
                    ],
                    "paddingAll": "15px"
                }
            }
        ]
    }
    return FlexSendMessage(alt_text="大型アップデート情報", contents=announcement)
