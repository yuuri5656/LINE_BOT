"""
チップ送受信機能のFlexMessage生成
"""
from linebot.models import FlexSendMessage
from datetime import datetime


def get_chip_transfer_guide_flex():
    """チップ送受信案内"""
    return FlexSendMessage(
        alt_text="チップ送受信ガイド",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "チップ送受信",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": "ユーザーID（@付き）を入力してください",
                                "size": "sm",
                                "color": "#999999"
                            },
                            {
                                "type": "text",
                                "text": "例：@U1234567890abcdef",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "wrap": True
                            }
                        ]
                    }
                ]
            }
        }
    )


def get_chip_amount_input_flex(to_user_id: str):
    """チップ枚数入力案内"""
    return FlexSendMessage(
        alt_text="チップ枚数入力",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "送信枚数を入力",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"送信先: {to_user_id}",
                                "size": "sm",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": "送信枚数を数字で入力してください",
                                "size": "sm",
                                "color": "#999999",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "※基本チップのみ送受信可能です",
                                "size": "xs",
                                "color": "#ff9999"
                            }
                        ]
                    }
                ]
            }
        }
    )


def get_chip_transfer_success_flex(to_user_id: str, amount: int, from_balance: int, to_balance: int = None):
    """チップ送信成功"""
    contents = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "✅ チップ送信完了",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#00aa00"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "margin": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "送信先:",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": to_user_id,
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 4
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "margin": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "送信枚数:",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"{amount}枚",
                                    "weight": "bold",
                                    "color": "#ff0000",
                                    "size": "sm",
                                    "flex": 4
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "margin": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "残高:",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"{from_balance}枚",
                                    "weight": "bold",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 4
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    return FlexSendMessage(
        alt_text="チップ送信完了",
        contents=contents
    )


def get_chip_transfer_error_flex(error_message: str, error_type: str = 'general'):
    """チップ送信エラー"""
    color_map = {
        'insufficient': '#ff9999',
        'validation': '#ffaa00',
        'user_not_found': '#ff6666',
        'general': '#ff0000'
    }
    color = color_map.get(error_type, '#ff0000')

    return FlexSendMessage(
        alt_text="チップ送信エラー",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "❌ エラー",
                        "weight": "bold",
                        "size": "xl",
                        "color": color
                    },
                    {
                        "type": "text",
                        "text": error_message,
                        "margin": "md",
                        "size": "sm",
                        "wrap": True,
                        "color": "#666666"
                    }
                ]
            }
        }
    )


def get_chip_receive_notification_flex(from_user_id: str, amount: int, new_balance: int):
    """チップ受信通知"""
    return FlexSendMessage(
        alt_text="チップを受け取りました",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎁 チップを受け取りました",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#ff6600"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "margin": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "送信元:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": from_user_id,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 4
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "margin": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "受取枚数:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{amount}枚",
                                        "weight": "bold",
                                        "color": "#ff0000",
                                        "size": "sm",
                                        "flex": 4
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "margin": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "残高:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{new_balance}枚",
                                        "weight": "bold",
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 4
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    )
