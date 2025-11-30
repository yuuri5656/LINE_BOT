"""
株式トレード用FlexMessageテンプレート
"""
from linebot.models import FlexSendMessage, ImageSendMessage
from typing import List, Dict, Optional
import urllib.parse


def get_stock_dashboard(user_id: str, has_account: bool) -> FlexSendMessage:
    """
    株式ダッシュボード（カルーセル型）

    Args:
        user_id: ユーザーID
        has_account: 株式口座の有無
    """
    bubbles = []

    # 1. 株式購入
    buy_bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📈", "size": "xxl", "align": "center", "color": "#FFFFFF"},
                {"type": "text", "text": "株式を購入", "size": "lg", "align": "center", "weight": "bold", "color": "#FFFFFF", "margin": "md"}
            ],
            "backgroundColor": "#2196F3",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "銘柄一覧から購入する株式を選択できます", "wrap": True, "color": "#666666", "size": "sm"}
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
                        "label": "銘柄一覧を見る",
                        "data": "action=stock_list"
                    },
                    "style": "primary",
                    "color": "#4CAF50"
                }
            ],
            "paddingAll": "15px"
        }
    }
    bubbles.append(buy_bubble)

    # 2. 保有株情報
    holdings_bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "💼", "size": "xxl", "align": "center", "color": "#FFFFFF"},
                {"type": "text", "text": "保有株情報", "size": "lg", "align": "center", "weight": "bold", "color": "#FFFFFF", "margin": "md"}
            ],
            "backgroundColor": "#FF9800",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "現在保有している株式の情報を確認できます", "wrap": True, "color": "#666666", "size": "sm"}
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
                        "label": "保有株を確認",
                        "data": "action=my_holdings"
                    },
                    "style": "primary",
                    "color": "#FF9800"
                }
            ],
            "paddingAll": "15px"
        }
    }
    bubbles.append(holdings_bubble)

    # 3. 市場情報
    market_bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📊", "size": "xxl", "align": "center", "color": "#FFFFFF"},
                {"type": "text", "text": "市場情報", "size": "lg", "align": "center", "weight": "bold", "color": "#FFFFFF", "margin": "md"}
            ],
            "backgroundColor": "#9C27B0",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "最新の経済ニュースとイベント情報", "wrap": True, "color": "#666666", "size": "sm"}
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
                        "label": "市場ニュース",
                        "data": "action=market_news"
                    },
                    "style": "primary",
                    "color": "#9C27B0"
                }
            ],
            "paddingAll": "15px"
        }
    }
    bubbles.append(market_bubble)

    return FlexSendMessage(
        alt_text="株式ダッシュボード",
        contents={"type": "carousel", "contents": bubbles}
    )


def get_stock_list_carousel(stocks: List[Dict], page: int = 0, per_page: int = 5) -> FlexSendMessage:
    """
    銘柄一覧カルーセル

    Args:
        stocks: 銘柄リスト
        page: ページ番号
        per_page: 1ページあたりの表示数
    """
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_stocks = stocks[start_idx:end_idx]

    bubbles = []
    for stock in page_stocks:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": stock['symbol_code'], "size": "xl", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": stock['name'], "size": "sm", "color": "#FFFFFF", "align": "center", "margin": "md", "wrap": True}
                ],
                "backgroundColor": "#2196F3",
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
                            {"type": "text", "text": "現在値", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{stock['current_price']:,}", "size": "lg", "weight": "bold", "color": "#4CAF50", "flex": 5, "align": "end"}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "セクター", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": stock['sector'], "size": "sm", "flex": 5, "align": "end", "wrap": True}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "配当利回り", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"{stock['dividend_yield']:.2f}%", "size": "sm", "flex": 5, "align": "end"}
                        ],
                        "margin": "md"
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
                            "label": "詳細を見る",
                            "data": f"action=stock_detail&symbol={stock['symbol_code']}"
                        },
                        "style": "primary",
                        "color": "#2196F3"
                    }
                ],
                "paddingAll": "15px"
            }
        }
        bubbles.append(bubble)

    return FlexSendMessage(
        alt_text="銘柄一覧",
        contents={"type": "carousel", "contents": bubbles}
    )


def get_stock_detail_flex(stock: Dict, has_holding: bool = False) -> FlexSendMessage:
    """
    銘柄詳細FlexMessage

    Args:
        stock: 銘柄情報
        has_holding: 保有株があるか
    """
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": stock['symbol_code'], "size": "xl", "weight": "bold", "color": "#FFFFFF"},
                {"type": "text", "text": stock['name'], "size": "md", "color": "#FFFFFF", "margin": "sm"}
            ],
            "backgroundColor": "#2196F3",
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
                        {"type": "text", "text": "現在値", "size": "sm", "color": "#666666", "flex": 3},
                        {"type": "text", "text": f"¥{stock['current_price']:,}", "size": "xxl", "weight": "bold", "color": "#4CAF50", "flex": 7, "align": "end"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _create_info_row("セクター", stock['sector']),
                        _create_info_row("時価総額", f"¥{stock['market_cap']:,}" if stock.get('market_cap') else "N/A"),
                        _create_info_row("配当利回り", f"{stock['dividend_yield']:.2f}%"),
                    ],
                    "margin": "lg",
                    "spacing": "md"
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "企業説明", "size": "sm", "color": "#666666", "weight": "bold"},
                        {"type": "text", "text": stock.get('description', '情報なし'), "size": "xs", "color": "#999999", "wrap": True, "margin": "sm"}
                    ],
                    "margin": "lg"
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
                        "label": "購入する",
                        "data": f"action=buy_stock&symbol={stock['symbol_code']}"
                    },
                    "style": "primary",
                    "color": "#4CAF50"
                }
            ] + ([{
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "売却する",
                    "data": f"action=sell_stock&symbol={stock['symbol_code']}"
                },
                "style": "primary",
                "color": "#F44336",
                "margin": "md"
            }] if has_holding else []),
            "paddingAll": "15px"
        }
    }

    return FlexSendMessage(alt_text=f"{stock['name']} 詳細", contents=bubble)


def get_holdings_carousel(holdings: List[Dict]) -> FlexSendMessage:
    """
    保有株一覧カルーセル

    Args:
        holdings: 保有株リスト
    """
    bubbles = []

    for holding in holdings:
        profit_color = "#4CAF50" if holding['profit_loss'] >= 0 else "#F44336"
        profit_sign = "+" if holding['profit_loss'] >= 0 else ""

        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": holding['symbol_code'], "size": "xl", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": holding['name'], "size": "sm", "color": "#FFFFFF", "align": "center", "margin": "md", "wrap": True}
                ],
                "backgroundColor": "#FF9800",
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
                            {"type": "text", "text": "保有数", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"{holding['quantity']}株", "size": "sm", "flex": 5, "align": "end", "weight": "bold"}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "平均取得価格", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{holding['average_price']:,.2f}", "size": "sm", "flex": 5, "align": "end"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "現在値", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{holding['current_price']:,}", "size": "sm", "flex": 5, "align": "end", "weight": "bold"}
                        ],
                        "margin": "md"
                    },
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "評価損益", "size": "sm", "color": "#666666", "flex": 3, "weight": "bold"},
                            {"type": "text", "text": f"{profit_sign}¥{holding['profit_loss']:,.0f}", "size": "md", "flex": 5, "align": "end", "weight": "bold", "color": profit_color}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "", "size": "sm", "flex": 3},
                            {"type": "text", "text": f"({profit_sign}{holding['profit_loss_rate']:,.1f}%)", "size": "sm", "flex": 5, "align": "end", "color": profit_color}
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
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "詳細を見る",
                            "data": f"action=stock_detail&symbol={holding['symbol_code']}"
                        },
                        "style": "primary",
                        "color": "#FF9800"
                    }
                ],
                "paddingAll": "15px"
            }
        }
        bubbles.append(bubble)

    return FlexSendMessage(
        alt_text="保有株一覧",
        contents={"type": "carousel", "contents": bubbles}
    )


def get_trade_confirmation_flex(stock_info: Dict, trade_type: str, quantity: int) -> FlexSendMessage:
    """
    取引確認FlexMessage

    Args:
        stock_info: 銘柄情報
        trade_type: 'buy' or 'sell'
        quantity: 数量
    """
    total_amount = stock_info['current_price'] * quantity
    action_text = "購入" if trade_type == 'buy' else "売却"
    color = "#4CAF50" if trade_type == 'buy' else "#F44336"

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"⚠️ {action_text}確認", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
            ],
            "backgroundColor": color,
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "以下の内容で取引を実行します", "size": "sm", "color": "#666666"},
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _create_info_row("銘柄コード", stock_info['symbol_code']),
                        _create_info_row("銘柄名", stock_info['name']),
                        _create_info_row("単価", f"¥{stock_info['current_price']:,}"),
                        _create_info_row("数量", f"{quantity}株"),
                        {"type": "separator", "margin": "md"},
                        {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                                {"type": "text", "text": "合計金額", "size": "md", "color": "#333333", "flex": 3, "weight": "bold"},
                                {"type": "text", "text": f"¥{total_amount:,}", "size": "xl", "weight": "bold", "color": color, "flex": 7, "align": "end"}
                            ],
                            "margin": "md"
                        }
                    ],
                    "margin": "lg",
                    "spacing": "md"
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
                        "label": f"{action_text}を確定",
                        "data": f"action=confirm_{trade_type}&symbol={stock_info['symbol_code']}&quantity={quantity}"
                    },
                    "style": "primary",
                    "color": color
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "キャンセル",
                        "data": "action=cancel_trade"
                    },
                    "style": "secondary",
                    "margin": "md"
                }
            ],
            "paddingAll": "15px"
        }
    }

    return FlexSendMessage(alt_text=f"{action_text}確認", contents=bubble)


def get_trade_result_flex(success: bool, trade_type: str, result_data: Optional[Dict] = None, error_message: str = "") -> FlexSendMessage:
    """
    取引結果FlexMessage

    Args:
        success: 成功フラグ
        trade_type: 'buy' or 'sell'
        result_data: 取引データ
        error_message: エラーメッセージ
    """
    action_text = "購入" if trade_type == 'buy' else "売却"

    if success and result_data:
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"✅ {action_text}完了", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#4CAF50",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{action_text}が正常に完了しました", "size": "sm", "color": "#666666"},
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            _create_info_row("銘柄コード", result_data['symbol_code']),
                            _create_info_row("銘柄名", result_data['name']),
                            _create_info_row("単価", f"¥{result_data['price']:,}"),
                            _create_info_row("数量", f"{result_data['quantity']}株"),
                            _create_info_row("合計金額", f"¥{result_data['total_amount']:,.0f}"),
                        ],
                        "margin": "lg",
                        "spacing": "md"
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
                            "label": "保有株を確認",
                            "data": "action=my_holdings"
                        },
                        "style": "primary",
                        "color": "#FF9800"
                    }
                ],
                "paddingAll": "15px"
            }
        }
    else:
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"❌ {action_text}失敗", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#F44336",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": error_message or f"{action_text}処理中にエラーが発生しました", "wrap": True, "color": "#666666", "size": "sm"}
                ],
                "paddingAll": "20px"
            }
        }

    return FlexSendMessage(alt_text=f"{action_text}結果", contents=bubble)


def get_account_registration_flex(accounts: List[Dict]) -> FlexSendMessage:
    """
    株式口座登録FlexMessage

    Args:
        accounts: 銀行口座リスト
    """
    if len(accounts) == 1:
        # 口座が1つの場合は自動登録確認
        account = accounts[0]
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "📋 株式口座登録", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#2196F3",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "以下の銀行口座と連携した株式口座を開設します", "wrap": True, "color": "#666666", "size": "sm"},
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            _create_info_row("支店", f"{account['branch_code']} - {account['branch_name']}"),
                            _create_info_row("口座番号", account['account_number']),
                            _create_info_row("残高", f"¥{account['balance']:,.0f}"),
                        ],
                        "margin": "lg",
                        "spacing": "md"
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
                            "label": "登録する",
                            "data": f"action=confirm_stock_account&account_id={account['account_id']}"
                        },
                        "style": "primary",
                        "color": "#4CAF50"
                    }
                ],
                "paddingAll": "15px"
            }
        }
    else:
        # 口座が複数の場合は選択画面
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "📋 口座選択", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#2196F3",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "連携する銀行口座を選択してください", "wrap": True, "color": "#666666", "size": "sm"}
                ] + [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"{acc['branch_code']}-{acc['account_number']}", "size": "sm", "weight": "bold"},
                            {"type": "text", "text": f"残高: ¥{acc['balance']:,.0f}", "size": "xs", "color": "#666666"}
                        ],
                        "margin": "lg",
                        "action": {
                            "type": "postback",
                            "data": f"action=select_stock_account&account_id={acc['account_id']}"
                        }
                    }
                    for acc in accounts
                ],
                "paddingAll": "20px"
            }
        }

    return FlexSendMessage(alt_text="株式口座登録", contents=bubble)


def _create_info_row(label: str, value: str) -> Dict:
    """情報行を作成（ヘルパー関数）"""
    return {
        "type": "box",
        "layout": "baseline",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#666666", "flex": 3},
            {"type": "text", "text": value, "size": "sm", "flex": 7, "align": "end", "wrap": True}
        ]
    }
