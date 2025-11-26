"""
ショップ用FlexMessageテンプレート
"""
from linebot.models import FlexSendMessage
from typing import List, Dict


def get_shop_home_carousel(categories: List[Dict]) -> FlexSendMessage:
    """ショップホーム画面（カルーセル型）"""
    bubbles = []

    for cat in categories:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": cat['icon'],
                        "size": "xxl",
                        "align": "center",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": cat['name'],
                        "size": "lg",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
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
                        "text": cat['description'],
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm"
                    }
                ],
                "spacing": "md",
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "商品を見る",
                            "data": f"action=shop_category&category={cat['code']}"
                        },
                        "style": "primary",
                        "color": "#4CAF50"
                    }
                ],
                "paddingAll": "15px"
            }
        }
        bubbles.append(bubble)

    return FlexSendMessage(
        alt_text="ショップ",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )


def get_category_items_flex(category_name: str, items: List[Dict]) -> FlexSendMessage:
    """カテゴリ内の商品一覧（属性対応版）"""
    contents = []

    for item in items:
        item_box = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": item['name'],
                            "weight": "bold",
                            "size": "md",
                            "flex": 0
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": item['description'],
                    "size": "xs",
                    "color": "#999999",
                    "margin": "sm",
                    "wrap": True
                }
            ],
            "margin": "lg"
        }

        # 属性から動的に情報を構築
        attrs = item.get('attributes', {})

        # チップ商品の場合
        if 'chip_amount' in attrs:
            chip_amount = attrs.get('chip_amount', 0)
            bonus_chip = attrs.get('bonus_chip', 0)

            chip_info = {
                "type": "box",
                "layout": "baseline",
                "contents": [
                    {
                        "type": "text",
                        "text": f"💰 {chip_amount}枚",
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0
                    }
                ],
                "margin": "sm"
            }
            item_box["contents"].append(chip_info)

            if bonus_chip > 0:
                bonus_info = {
                    "type": "text",
                    "text": f"🎁 ボーナス +{bonus_chip}枚",
                    "size": "xs",
                    "color": "#FF6B6B",
                    "weight": "bold",
                    "margin": "xs"
                }
                item_box["contents"].append(bonus_info)

        # ブースターの場合（将来対応）
        if 'boost_rate' in attrs:
            boost_rate = attrs.get('boost_rate', 0)
            duration = attrs.get('duration_days', 0)

            boost_info = {
                "type": "text",
                "text": f"🚀 {boost_rate}倍速 ({duration}日間)",
                "size": "sm",
                "color": "#4CAF50",
                "margin": "sm"
            }
            item_box["contents"].append(boost_info)

        # 価格とボタン
        footer = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{item['price']} JPY",
                    "size": "lg",
                    "weight": "bold",
                    "color": "#4CAF50",
                    "flex": 1
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "購入",
                        "data": f"action=shop_buy&item_id={item['item_id']}"
                    },
                    "style": "primary",
                    "color": "#4CAF50",
                    "flex": 1
                }
            ],
            "margin": "md"
        }
        item_box["contents"].append(footer)

        contents.append(item_box)
        contents.append({"type": "separator", "margin": "lg"})

    # 最後のセパレータを削除
    if contents and contents[-1].get("type") == "separator":
        contents.pop()

    return FlexSendMessage(
        alt_text=f"{category_name}の商品一覧",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": category_name,
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF"
                    }
                ],
                "backgroundColor": "#FF6B6B",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": contents,
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "ショップホームに戻る",
                            "data": "action=shop_home"
                        },
                        "style": "secondary"
                    }
                ],
                "paddingAll": "15px"
            }
        }
    )


def get_payment_account_registration_flex() -> FlexSendMessage:
    """ショップ支払い用口座登録案内"""
    return FlexSendMessage(
        alt_text="ショップ支払い用口座の登録",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💳",
                        "size": "xxl",
                        "align": "center",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": "支払い用口座の登録",
                        "size": "lg",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#4CAF50",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ショップでの購入には、支払い用口座の登録が必要です。",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "登録手順",
                        "weight": "bold",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "1. 支店番号（3桁）\n2. 口座番号（7桁）\n3. 氏名（半角カナ）\n4. 暗証番号（4桁）",
                        "size": "xs",
                        "color": "#999999",
                        "margin": "md",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "※既にお持ちの銀行口座を登録してください",
                        "size": "xxs",
                        "color": "#FF6B6B",
                        "margin": "md",
                        "wrap": True
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "口座を登録する",
                            "data": "action=register_payment_account"
                        },
                        "style": "primary",
                        "color": "#4CAF50"
                    }
                ],
                "paddingAll": "15px"
            }
        }
    )


def get_purchase_success_flex(item_name: str, chips_received: int, new_balance: int) -> FlexSendMessage:
    """購入成功メッセージ"""
    return FlexSendMessage(
        alt_text="購入完了",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "✅",
                        "size": "xxl",
                        "align": "center",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": "購入完了",
                        "size": "xl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#4CAF50",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "商品:",
                                "size": "sm",
                                "color": "#999999",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": item_name,
                                "size": "sm",
                                "color": "#111111",
                                "margin": "sm",
                                "wrap": True
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "獲得チップ:",
                                "size": "sm",
                                "color": "#999999",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": f"{chips_received}枚",
                                "size": "sm",
                                "color": "#FF6B6B",
                                "weight": "bold",
                                "margin": "sm"
                            }
                        ],
                        "margin": "md"
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
                                "text": "新しい残高:",
                                "size": "md",
                                "color": "#111111",
                                "weight": "bold",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": f"{new_balance}枚",
                                "size": "md",
                                "color": "#4CAF50",
                                "weight": "bold",
                                "margin": "sm"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    )
