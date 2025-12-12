"""
懲役システムの Flex メッセージテンプレート
"""
from linebot.models import FlexSendMessage


def get_prison_work_result_flex(result: dict) -> FlexSendMessage:
    """
    懲役中の?労働実行結果を表示
    
    Args:
        result: do_prison_work() の戻り値
    """
    
    # メッセージテキスト
    message_text = result.get('message', 'エラーが発生しました')
    
    # ステータスカラー
    if result.get('quota_completed'):
        status_color = '#FF6B6B'  # 赤：ノルマ達成
    else:
        status_color = '#4ECDC4'  # 青：進行中
    
    flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "【懲役中】 ?労働実行結果",
                    "weight": "bold",
                    "size": "lg",
                    "color": status_color
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": message_text,
                    "wrap": True,
                    "size": "sm",
                    "color": "#666666"
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
                                    "text": "給与:",
                                    "color": "#999999",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"¥{result.get('salary', 0):,}",
                                    "color": "#FFFFFF",
                                    "size": "sm",
                                    "flex": 2,
                                    "align": "end"
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
                                    "text": "給付金口座残高:",
                                    "color": "#999999",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"¥{result.get('balance_after', 0):,}",
                                    "color": "#FFFFFF",
                                    "size": "sm",
                                    "flex": 2,
                                    "align": "end"
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
                                    "text": "残り懲役日数:",
                                    "color": "#999999",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": f"{result.get('remaining_days', 0)}日",
                                    "color": "#FFFFFF",
                                    "size": "sm",
                                    "flex": 2,
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "稼いだ給与は犯罪者更生給付金口座へ振り込まれ、市民に配布されます",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center",
                    "wrap": True
                }
            ]
        }
    }
    
    return FlexSendMessage(
        alt_text="【懲役中】 ?労働実行結果",
        contents=flex_content
    )


def get_prison_status_flex(prisoner_status: dict, user_id: str) -> FlexSendMessage:
    """
    懲役ステータス表示
    """
    
    if not prisoner_status['is_imprisoned']:
        flex_content = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "懲役情報",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": "このユーザーは懲役中ではありません",
                        "wrap": True,
                        "color": "#999999"
                    }
                ]
            }
        }
    else:
        flex_content = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"【懲役中】 {user_id}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#FF6B6B"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "残り懲役日数:",
                                "color": "#999999",
                                "size": "sm",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": f"{prisoner_status.get('remaining_days', 0)}日",
                                "color": "#FF6B6B",
                                "size": "lg",
                                "flex": 1,
                                "align": "end",
                                "weight": "bold"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "釈放日:",
                                "color": "#999999",
                                "size": "sm",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": str(prisoner_status.get('end_date', 'N/A')),
                                "color": "#FFFFFF",
                                "size": "sm",
                                "flex": 1,
                                "align": "end"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "1日のノルマ:",
                                "color": "#999999",
                                "size": "sm",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": f"{prisoner_status.get('daily_quota', 0)}回",
                                "color": "#FFFFFF",
                                "size": "sm",
                                "flex": 1,
                                "align": "end"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {
                                "type": "text",
                                "text": "本日の進捗:",
                                "color": "#999999",
                                "size": "sm",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": f"{prisoner_status.get('completed_today', 0)}/{prisoner_status.get('daily_quota', 0)}",
                                "color": "#4ECDC4",
                                "size": "sm",
                                "flex": 1,
                                "align": "end",
                                "weight": "bold"
                            }
                        ]
                    }
                ]
            }
        }
    
    return FlexSendMessage(
        alt_text="懲役情報",
        contents=flex_content
    )
