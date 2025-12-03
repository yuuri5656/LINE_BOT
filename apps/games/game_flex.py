"""
ゲーム選択用FlexMessageテンプレート
"""
from linebot.models import FlexSendMessage
from typing import List, Dict


def get_game_selection_carousel() -> FlexSendMessage:
    """
    カジノゲーム選択カルーセル（カジュアルデザイン）

    Returns:
        FlexSendMessage: ゲーム選択カルーセル
    """
    games = [
        {
            "name": "ブラックジャック",
            "type": "blackjack",
            "icon": "🃏",
            "description": "ディーラーと対戦して21に近づけよう！",
            "min_bet": 10,
            "color": "#2196F3"
        },
        # 将来的に追加予定のゲーム
        # {
        #     "name": "ルーレット",
        #     "type": "roulette",
        #     "icon": "🎰",
        #     "description": "赤か黒か運試しの王道ゲーム",
        #     "min_bet": 10,
        #     "color": "#F44336"
        # },
        # {
        #     "name": "スロット",
        #     "type": "slot",
        #     "icon": "🎰",
        #     "description": "3つ揃えば大当たり！",
        #     "min_bet": 5,
        #     "color": "#FF9800"
        # }
    ]

    bubbles = []

    for game in games:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": game["icon"],
                        "size": "xxl",
                        "align": "center",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": game["name"],
                        "size": "lg",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "margin": "md"
                    }
                ],
                "backgroundColor": game["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": game["description"],
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "最小ベット",
                                "size": "xs",
                                "color": "#999999",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": f"{game['min_bet']}チップ～",
                                "size": "xs",
                                "color": "#111111",
                                "align": "end"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "paddingAll": "20px",
                "spacing": "md"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "遊ぶ",
                            "data": f"action=select_game&game_type={game['type']}&min_bet={game['min_bet']}"
                        },
                        "style": "primary",
                        "color": game["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "15px"
            }
        }
        bubbles.append(bubble)

    return FlexSendMessage(
        alt_text="カジノゲーム",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )


def get_insufficient_chips_message(current_balance: int, min_required: int) -> FlexSendMessage:
    """
    チップ不足メッセージ

    Args:
        current_balance: 現在のチップ残高
        min_required: 最小必要チップ

    Returns:
        FlexSendMessage: チップ不足メッセージ
    """
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "⚠️",
                    "size": "xxl",
                    "align": "center",
                    "color": "#FFFFFF"
                },
                {
                    "type": "text",
                    "text": "チップ不足",
                    "size": "xl",
                    "align": "center",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "margin": "md"
                }
            ],
            "backgroundColor": "#FF6B6B",
            "paddingAll": "30px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "ゲームをプレイするには、より多くのチップが必要です。",
                    "wrap": True,
                    "color": "#666666",
                    "size": "sm",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": "現在の残高",
                            "size": "sm",
                            "color": "#666666",
                            "flex": 3
                        },
                        {
                            "type": "text",
                            "text": f"{current_balance}チップ",
                            "size": "sm",
                            "color": "#FF6B6B",
                            "weight": "bold",
                            "flex": 4,
                            "align": "end"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": "必要最小額",
                            "size": "sm",
                            "color": "#666666",
                            "flex": 3
                        },
                        {
                            "type": "text",
                            "text": f"{min_required}チップ",
                            "size": "sm",
                            "color": "#4CAF50",
                            "weight": "bold",
                            "flex": 4,
                            "align": "end"
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "💡 ショップでチップを購入できます",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center",
                    "margin": "xl",
                    "wrap": True
                }
            ],
            "paddingAll": "25px",
            "spacing": "md"
        }
    }

    return FlexSendMessage(
        alt_text="チップ不足",
        contents=bubble
    )
