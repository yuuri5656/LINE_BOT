"""
ブラックジャック用FlexMessageテンプレート
"""
from linebot.models import FlexSendMessage
from typing import List, Dict


def get_betting_screen(current_bet: int, chip_balance: int, game_type: str = "blackjack") -> FlexSendMessage:
    """
    ベット額選択画面（カジノチップボタン式）

    Args:
        current_bet: 現在のベット額
        chip_balance: チップ残高
        game_type: ゲームタイプ

    Returns:
        FlexSendMessage: ベット選択画面
    """
    # 最大ベット制限
    max_bet = min(2000, chip_balance)
    can_add_10 = current_bet + 10 <= max_bet
    can_add_100 = current_bet + 100 <= max_bet
    can_add_1000 = current_bet + 1000 <= max_bet
    can_confirm = current_bet >= 10  # 最小ベット10チップ

    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "MAXBET",
                            "size": "xs",
                            "color": "#FFD700",
                            "weight": "bold",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "2,000",
                            "size": "md",
                            "color": "#FFD700",
                            "weight": "bold",
                            "flex": 0,
                            "margin": "md"
                        },
                        {
                            "type": "filler"
                        },
                        {
                            "type": "text",
                            "text": "MINBET",
                            "size": "xs",
                            "color": "#FFD700",
                            "weight": "bold",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "10",
                            "size": "md",
                            "color": "#FFD700",
                            "weight": "bold",
                            "flex": 0,
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#1B3A5F",
                    "paddingAll": "12px",
                    "cornerRadius": "5px 5px 0px 0px"
                }
            ],
            "backgroundColor": "#0A1929",
            "paddingAll": "0px",
            "spacing": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # 現在のベット額表示
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "TOTAL",
                            "size": "xs",
                            "color": "#CCCCCC",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": str(current_bet),
                            "size": "xxl",
                            "weight": "bold",
                            "color": "#FFD700",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#1B3A5F",
                    "cornerRadius": "5px",
                    "paddingAll": "20px",
                    "margin": "none",
                    "borderWidth": "2px",
                    "borderColor": "#2E5A8A"
                },
                # チップボタン
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🔵",
                                    "size": "xxl",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": "10",
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#FFFFFF",
                                    "align": "center"
                                }
                            ],
                            "action": {
                                "type": "postback",
                                "data": f"action=add_bet&amount=10&game_type={game_type}"
                            } if can_add_10 else None,
                            "backgroundColor": "#4169E1" if can_add_10 else "#555555",
                            "cornerRadius": "50px",
                            "paddingAll": "15px",
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🟢",
                                    "size": "xxl",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": "100",
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#FFFFFF",
                                    "align": "center"
                                }
                            ],
                            "action": {
                                "type": "postback",
                                "data": f"action=add_bet&amount=100&game_type={game_type}"
                            } if can_add_100 else None,
                            "backgroundColor": "#32CD32" if can_add_100 else "#555555",
                            "cornerRadius": "50px",
                            "paddingAll": "15px",
                            "flex": 1,
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🔴",
                                    "size": "xxl",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": "1000",
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#FFFFFF",
                                    "align": "center"
                                }
                            ],
                            "action": {
                                "type": "postback",
                                "data": f"action=add_bet&amount=1000&game_type={game_type}"
                            } if can_add_1000 else None,
                            "backgroundColor": "#DC143C" if can_add_1000 else "#555555",
                            "cornerRadius": "50px",
                            "paddingAll": "15px",
                            "flex": 1,
                            "margin": "md"
                        }
                    ],
                    "margin": "xl",
                    "spacing": "md"
                },
                # 残高表示
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "所持チップ",
                            "size": "xs",
                            "color": "#999999",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": f"{chip_balance}",
                            "size": "sm",
                            "color": "#FFD700",
                            "weight": "bold",
                            "align": "end"
                        }
                    ],
                    "margin": "xl"
                }
            ],
            "paddingAll": "25px",
            "backgroundColor": "#0A1929",
            "spacing": "md"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ベット\n-BET-",
                                    "size": "xs",
                                    "color": "#000000" if can_confirm else "#666666",
                                    "align": "center",
                                    "weight": "bold"
                                }
                            ],
                            "backgroundColor": "#C9A961" if can_confirm else "#555555",
                            "cornerRadius": "5px",
                            "paddingAll": "12px",
                            "action": {
                                "type": "postback",
                                "data": f"action=confirm_bet&game_type={game_type}"
                            } if can_confirm else None,
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "取消",
                                    "size": "xs",
                                    "color": "#FFFFFF",
                                    "align": "center",
                                    "weight": "bold"
                                }
                            ],
                            "backgroundColor": "#555555",
                            "cornerRadius": "5px",
                            "paddingAll": "12px",
                            "action": {
                                "type": "postback",
                                "data": f"action=reset_bet&game_type={game_type}"
                            },
                            "flex": 1,
                            "margin": "md"
                        }
                    ]
                }
            ],
            "paddingAll": "20px",
            "spacing": "sm",
            "backgroundColor": "#0A1929"
        }
    }

    return FlexSendMessage(
        alt_text="ベット額を選択",
        contents=bubble
    )


def get_game_screen(player_hand: List[Dict], dealer_hand: List[Dict],
                   player_total: int, dealer_showing: int,
                   bet_amount: int, can_double: bool = True,
                   hide_dealer_second: bool = True) -> FlexSendMessage:
    """
    ゲーム画面（プレイ中）

    Args:
        player_hand: プレイヤーの手札 [{'rank': 'A', 'suit': 'spades', 'emoji': '🂡'}]
        dealer_hand: ディーラーの手札
        player_total: プレイヤーの合計値
        dealer_showing: ディーラーの表示カード合計
        bet_amount: ベット額
        can_double: ダブルダウン可能か
        hide_dealer_second: ディーラーの2枚目を隠すか

    Returns:
        FlexSendMessage: ゲーム画面
    """
    # ディーラーのカード表示
    dealer_cards = []
    for i, card in enumerate(dealer_hand):
        if i == 1 and hide_dealer_second:
            dealer_cards.append("🂠")  # 伏せカード
        else:
            dealer_cards.append(card.get('emoji', '🂠'))

    # プレイヤーのカード表示
    player_cards = [card.get('emoji', '🂠') for card in player_hand]

    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # ヘッダー（カジノテーブル風）
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "BLACKJACK PAYS 3 TO 2",
                            "size": "xs",
                            "weight": "bold",
                            "color": "#FFD700",
                            "align": "center",
                            "flex": 1
                        }
                    ],
                    "backgroundColor": "#1B3A5F",
                    "paddingAll": "8px",
                    "cornerRadius": "5px",
                    "margin": "none"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Your turn",
                            "size": "sm",
                            "color": "#FFFFFF",
                            "flex": 0
                        },
                        {
                            "type": "filler"
                        },
                        {
                            "type": "text",
                            "text": f"BET: {bet_amount}",
                            "size": "sm",
                            "color": "#FFD700",
                            "weight": "bold",
                            "flex": 0
                        }
                    ],
                    "margin": "md"
                },
                # ディーラー
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "DEALER",
                            "size": "xs",
                            "color": "#999999",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": " ".join(dealer_cards),
                            "size": "xl",
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"Showing: {dealer_showing}" if hide_dealer_second else f"Total: {dealer_showing}",
                            "size": "sm",
                            "color": "#FFFFFF",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#1B3A5F",
                    "cornerRadius": "8px",
                    "paddingAll": "15px",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": "#2E5A8A"
                },
                # テーブル中央の装飾線
                {
                    "type": "separator",
                    "color": "#2E5A8A",
                    "margin": "lg"
                },
                # プレイヤー
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "YOUR HAND",
                            "size": "xs",
                            "color": "#999999",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": " ".join(player_cards),
                            "size": "xl",
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"Total: {player_total}",
                            "size": "lg",
                            "color": "#FFD700",
                            "weight": "bold",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#1B3A5F",
                    "cornerRadius": "8px",
                    "paddingAll": "15px",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": "#2E5A8A"
                }
            ],
            "paddingAll": "25px",
            "backgroundColor": "#0A1929",
            "spacing": "none"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ディール\n-DEAL-",
                                    "size": "xxs",
                                    "color": "#FFFFFF",
                                    "align": "center",
                                    "weight": "bold"
                                }
                            ],
                            "backgroundColor": "#C9A961",
                            "cornerRadius": "50px",
                            "paddingAll": "10px",
                            "flex": 0,
                            "width": "70px"
                        },
                        {
                            "type": "filler"
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ヒット",
                                    "size": "xs",
                                    "color": "#FFFFFF",
                                    "align": "center",
                                    "weight": "bold"
                                }
                            ],
                            "backgroundColor": "#4CAF50",
                            "cornerRadius": "5px",
                            "paddingAll": "10px",
                            "action": {
                                "type": "postback",
                                "data": "action=hit"
                            },
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "スタンド",
                                    "size": "xs",
                                    "color": "#FFFFFF",
                                    "align": "center",
                                    "weight": "bold"
                                }
                            ],
                            "backgroundColor": "#F44336",
                            "cornerRadius": "5px",
                            "paddingAll": "10px",
                            "action": {
                                "type": "postback",
                                "data": "action=stand"
                            },
                            "flex": 1,
                            "margin": "sm"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ダブルダウン",
                            "size": "xs",
                            "color": "#FFFFFF" if can_double else "#666666",
                            "align": "center",
                            "weight": "bold"
                        }
                    ],
                    "backgroundColor": "#FF9800" if can_double else "#333333",
                    "cornerRadius": "5px",
                    "paddingAll": "10px",
                    "action": {
                        "type": "postback",
                        "data": "action=double"
                    } if can_double else None,
                    "margin": "sm"
                } if True else {
                    "type": "text",
                    "text": "",
                    "size": "xxs"
                }
            ],
            "paddingAll": "20px",
            "spacing": "sm",
            "backgroundColor": "#0A1929"
        }
    }

    return FlexSendMessage(
        alt_text="ブラックジャック",
        contents=bubble
    )


def get_result_screen(player_hand: List[Dict], dealer_hand: List[Dict],
                     player_total: int, dealer_total: int,
                     result: str, bet_amount: int, payout: int,
                     chip_balance: int) -> FlexSendMessage:
    """
    結果画面

    Args:
        player_hand: プレイヤーの手札
        dealer_hand: ディーラーの手札
        player_total: プレイヤーの合計値
        dealer_total: ディーラーの合計値
        result: 結果 ('win', 'lose', 'push', 'blackjack')
        bet_amount: ベット額
        payout: 配当額（獲得チップ）
        chip_balance: 新しいチップ残高

    Returns:
        FlexSendMessage: 結果画面
    """
    # 結果テキストと色
    result_config = {
        'win': {'text': '🏆 WIN!', 'color': '#FFD700', 'bg': '#4CAF50'},
        'blackjack': {'text': '🎉 BLACKJACK!', 'color': '#FFD700', 'bg': '#9C27B0'},
        'lose': {'text': '💔 LOSE', 'color': '#FFFFFF', 'bg': '#FF6B6B'},
        'push': {'text': '🤝 PUSH', 'color': '#FFFFFF', 'bg': '#FF9800'},
        'bust': {'text': '💥 BUST!', 'color': '#FFFFFF', 'bg': '#DC143C'}
    }

    config = result_config.get(result, result_config['lose'])

    # カード表示
    dealer_cards = " ".join([card.get('emoji', '🂠') for card in dealer_hand])
    player_cards = " ".join([card.get('emoji', '🂠') for card in player_hand])

    # 収支計算
    net_gain = payout - bet_amount
    net_text = f"+{net_gain}" if net_gain > 0 else str(net_gain) if net_gain < 0 else "±0"
    net_color = "#4CAF50" if net_gain > 0 else "#FF6B6B" if net_gain < 0 else "#999999"

    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": config['text'],
                    "size": "xxl",
                    "weight": "bold",
                    "color": config['color'],
                    "align": "center"
                }
            ],
            "backgroundColor": config['bg'],
            "paddingAll": "30px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # ディーラーの手札
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "DEALER",
                            "size": "xs",
                            "color": "#999999",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": dealer_cards,
                            "size": "lg",
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"Total: {dealer_total}",
                            "size": "sm",
                            "color": "#FFFFFF",
                            "align": "center",
                            "margin": "xs"
                        }
                    ],
                    "backgroundColor": "#1A5F7A",
                    "cornerRadius": "10px",
                    "paddingAll": "15px"
                },
                # プレイヤーの手札
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "YOUR HAND",
                            "size": "xs",
                            "color": "#999999",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": player_cards,
                            "size": "lg",
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"Total: {player_total}",
                            "size": "sm",
                            "color": "#FFD700",
                            "weight": "bold",
                            "align": "center",
                            "margin": "xs"
                        }
                    ],
                    "backgroundColor": "#1A5F7A",
                    "cornerRadius": "10px",
                    "paddingAll": "15px",
                    "margin": "lg"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#FFD700"
                },
                # 収支情報
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ベット額",
                                    "size": "sm",
                                    "color": "#999999",
                                    "flex": 3
                                },
                                {
                                    "type": "text",
                                    "text": f"{bet_amount}チップ",
                                    "size": "sm",
                                    "color": "#FFFFFF",
                                    "flex": 4,
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
                                    "text": "配当",
                                    "size": "sm",
                                    "color": "#999999",
                                    "flex": 3
                                },
                                {
                                    "type": "text",
                                    "text": f"{payout}チップ",
                                    "size": "sm",
                                    "color": "#FFD700",
                                    "weight": "bold",
                                    "flex": 4,
                                    "align": "end"
                                }
                            ],
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "収支",
                                    "size": "md",
                                    "color": "#FFFFFF",
                                    "weight": "bold",
                                    "flex": 3
                                },
                                {
                                    "type": "text",
                                    "text": f"{net_text}チップ",
                                    "size": "md",
                                    "color": net_color,
                                    "weight": "bold",
                                    "flex": 4,
                                    "align": "end"
                                }
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "残高",
                                    "size": "sm",
                                    "color": "#999999",
                                    "flex": 3
                                },
                                {
                                    "type": "text",
                                    "text": f"{chip_balance}チップ",
                                    "size": "sm",
                                    "color": "#FFD700",
                                    "flex": 4,
                                    "align": "end"
                                }
                            ],
                            "margin": "md"
                        }
                    ],
                    "margin": "xl",
                    "spacing": "sm"
                }
            ],
            "paddingAll": "25px",
            "backgroundColor": "#0D3B4A",
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
                        "label": "もう一度プレイ",
                        "data": "action=select_game&game_type=blackjack&min_bet=10"
                    },
                    "style": "primary",
                    "color": "#4CAF50",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "ゲームメニューへ",
                        "text": "?ゲーム"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px",
            "spacing": "sm",
            "backgroundColor": "#0D3B4A"
        }
    }

    return FlexSendMessage(
        alt_text=f"ブラックジャック - {config['text']}",
        contents=bubble
    )
