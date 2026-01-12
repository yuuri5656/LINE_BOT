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

    # 4. 空売り情報
    short_bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📉", "size": "xxl", "align": "center", "color": "#FFFFFF"},
                {"type": "text", "text": "空売り状況", "size": "lg", "align": "center", "weight": "bold", "color": "#FFFFFF", "margin": "md"}
            ],
            "backgroundColor": "#607D8B",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "現在保有している空売りポジションを確認できます", "wrap": True, "color": "#666666", "size": "sm"}
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
                        "label": "空売りを確認",
                        "data": "action=my_short_positions"
                    },
                    "style": "primary",
                    "color": "#607D8B"
                }
            ],
            "paddingAll": "15px"
        }
    }
    bubbles.append(short_bubble)

    return FlexSendMessage(
        alt_text="株式ダッシュボード",
        contents={"type": "carousel", "contents": bubbles}
    )


def get_stock_list_carousel(stocks: List[Dict], page: int = 0, per_page: int = 10) -> FlexSendMessage:
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
        # 騰落率計算
        change_rate = stock.get('change_rate', 0)
        change_color = "#4CAF50" if change_rate >= 0 else "#F44336"
        change_arrow = "▲" if change_rate >= 0 else "▼"
        change_sign = "+" if change_rate > 0 else ""

        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": stock['symbol_code'], "size": "md", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": stock['name'], "size": "lg", "color": "#FFFFFF", "align": "center", "margin": "md", "wrap": True}
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
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": change_arrow, "size": "sm", "color": change_color, "flex": 0, "margin": "none"},
                            {"type": "text", "text": f"{change_sign}{change_rate:.2f}%", "size": "xs", "color": change_color, "flex": 0, "margin": "sm"},
                            {"type": "text", "text": f"¥{stock['current_price']:,}", "size": "xl", "weight": "bold", "color": "#333333", "flex": 1, "align": "end"}
                        ],
                        "alignItems": "center"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "セクター", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": stock['sector'], "size": "sm", "flex": 5, "align": "end", "wrap": True}
                        ],
                        "margin": "md"
                    }
                ],
                "paddingAll": "18px"
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


def get_stock_detail_flex(stock: Dict, has_holding: bool = False, has_short_position: bool = False) -> FlexSendMessage:
    """
    銘柄詳細FlexMessage

    Args:
        stock: 銘柄情報
        has_holding: 保有株があるか
        has_short_position: 空売りポジションがあるか
    """
    
    # ボタンリスト作成
    buttons = []
    
    # 1. 購入 (Buy)
    buttons.append({
        "type": "button",
        "action": {
            "type": "postback",
            "label": "購入する (現物)",
            "data": f"action=buy_stock&symbol={stock['symbol_code']}"
        },
        "style": "primary",
        "color": "#4CAF50"
    })

    # 2. 売却 (Sell) - 保有時のみ
    if has_holding:
        buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": "売却する (現物)",
                "data": f"action=sell_stock&symbol={stock['symbol_code']}"
            },
            "style": "primary",
            "color": "#F44336",
            "margin": "md"
        })

    # 3. 空売り (Sell Short) - 保有がない場合、または追加で空売り
    # 簡略化して常に表示、またはボタンテキストを変える？
    buttons.append({
        "type": "button",
        "action": {
            "type": "postback",
            "label": "空売りする",
            "data": f"action=sell_short&symbol={stock['symbol_code']}"
        },
        "style": "secondary",
        "color": "#607D8B",
        "margin": "md"
    })

    # 4. 買い戻し (Buy to Cover) - 空売りポジションがある場合のみ
    if has_short_position:
        buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": "買い戻す (返済)",
                "data": f"action=buy_to_cover&symbol={stock['symbol_code']}"
            },
            "style": "primary",
            "color": "#FF9800",
            "margin": "md"
        })


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
                        _create_info_row("前日終値", f"¥{stock.get('previous_close', 0):,}" if stock.get('previous_close') else "N/A"),
                        _create_info_row("高値", f"¥{stock.get('daily_high', 0):,}" if stock.get('daily_high') else "N/A"),
                        _create_info_row("安値", f"¥{stock.get('daily_low', 0):,}" if stock.get('daily_low') else "N/A"),
                        _create_info_row("出来高", f"{stock.get('volume', 0):,}株" if stock.get('volume') else "N/A"),
                        _create_info_row("売買代金", f"¥{stock.get('trading_value', 0):,.0f}" if stock.get('trading_value') else "N/A"), # Note: trading_value not in model yet, might need to calculate? Or just use volume * current_price approx?
                        # Actually trading_value is not in StockSymbol directly easily. 
                        # Let's approximate or skip if not available. Wait, user asked for it. 
                        # Volume is in price_history. StockSymbol has current_price.
                        # Maybe just "Volume" is enough? Or calculate approximate.
                        # Let's use simple calculation or check if service provides it.
                        _create_info_row("時価総額", f"¥{stock['market_cap']:,}" if stock.get('market_cap') else "N/A"),
                        _create_info_row("配当利回り", f"{stock['dividend_yield']:.2f}%"),
                        _create_info_row("空売り残", f"{stock.get('short_interest', 0):,}株"),
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
            "contents": buttons,
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
                            {"type": "text", "text": "取得総額", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{holding['total_cost']:,.0f}", "size": "sm", "flex": 5, "align": "end"}
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
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "評価額", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{holding['market_value']:,.0f}", "size": "sm", "flex": 5, "align": "end", "weight": "bold"}
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
                            {"type": "text", "text": " ", "size": "sm", "color": "#666666", "flex": 3},
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
    total_amount = stock_info['current_price'] * quantity
    
    if trade_type == 'buy':
        action_text = "購入"
        color = "#4CAF50"
    elif trade_type == 'sell':
        action_text = "売却"
        color = "#F44336"
    elif trade_type == 'short':
        action_text = "空売り"
        color = "#607D8B"
    elif trade_type == 'cover':
        action_text = "買い戻し"
        color = "#FF9800"
    else:
        action_text = "取引"
        color = "#999999"

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
    if trade_type == 'buy':
        action_text = "購入"
    elif trade_type == 'sell':
        action_text = "売却"
    elif trade_type == 'short':
        action_text = "空売り"
    elif trade_type == 'cover':
        action_text = "買い戻し"
    else:
        action_text = "取引"

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
                "backgroundColor": "#C62828",
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
                    {"type": "text", "text": "⚠️ 一度連携すると変更できません", "wrap": True, "color": "#F44336", "size": "xs", "weight": "bold", "margin": "sm"},
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            _create_info_row("名義", account.get('account_holder', 'N/A')),
                            _create_info_row("種別", account.get('account_type', 'N/A')),
                            _create_info_row("支店", f"{account['branch_code']} - {account['branch_name']}"),
                            _create_info_row("口座番号", account['account_number']),
                            _create_info_row("残高", f"¥{float(account['balance']):,.0f}"),
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
        account_boxes = []
        for i, acc in enumerate(accounts):
            if i > 0:
                account_boxes.append({"type": "separator", "margin": "lg"})
            account_boxes.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"📌 {acc.get('account_holder', 'N/A')}", "size": "md", "weight": "bold", "color": "#2196F3"},
                    {"type": "text", "text": f"種別: {acc.get('account_type', 'N/A')}", "size": "xs", "color": "#666666", "margin": "sm"},
                    {"type": "text", "text": f"{acc['branch_code']}-{acc['account_number']}", "size": "sm", "weight": "bold", "margin": "sm"},
                    {"type": "text", "text": f"残高: ¥{float(acc['balance']):,.0f}", "size": "xs", "color": "#666666"},
                    {"type": "text", "text": "👆 タップして選択", "size": "xxs", "color": "#999999", "align": "center", "margin": "sm"}
                ],
                "margin": "lg",
                "paddingAll": "15px",
                "backgroundColor": "#F5F5F5",
                "cornerRadius": "md",
                "action": {
                    "type": "postback",
                    "data": f"action=select_stock_account&account_id={acc['account_id']}"
                }
            })

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
                    {"type": "text", "text": "連携する銀行口座を選択してください", "wrap": True, "color": "#666666", "size": "sm"},
                    {"type": "text", "text": "⚠️ 一度連携すると変更できません", "wrap": True, "color": "#F44336", "size": "xs", "weight": "bold", "margin": "sm"}
                ] + account_boxes,
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


def get_short_positions_carousel(shorts: List[Dict]) -> FlexSendMessage:
    """
    空売り建玉一覧カルーセル

    Args:
        shorts: 空売りポジションリスト
    """
    bubbles = []

    for s in shorts:
        profit_color = "#4CAF50" if s['profit_loss'] >= 0 else "#F44336"
        profit_sign = "+" if s['profit_loss'] >= 0 else ""

        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": s['symbol_code'], "size": "xl", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": s['name'], "size": "sm", "color": "#FFFFFF", "align": "center", "margin": "md", "wrap": True}
                ],
                "backgroundColor": "#607D8B",
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
                            {"type": "text", "text": "数量", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"{s['quantity']}株", "size": "sm", "flex": 5, "align": "end", "weight": "bold"}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "売建単価", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{s['average_sell_price']:,.2f}", "size": "sm", "flex": 5, "align": "end"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "現在値", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"¥{s['current_price']:,}", "size": "sm", "flex": 5, "align": "end", "weight": "bold"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "返済期日", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"{s.get('due_date', 'N/A')}", "size": "sm", "flex": 5, "align": "end", "color": "#FF5722"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": "評価損益", "size": "sm", "color": "#666666", "flex": 3, "weight": "bold"},
                            {"type": "text", "text": f"{profit_sign}¥{s['profit_loss']:,.0f}", "size": "md", "flex": 5, "align": "end", "weight": "bold", "color": profit_color}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": " ", "size": "sm", "color": "#666666", "flex": 3},
                            {"type": "text", "text": f"({profit_sign}{s['profit_loss_rate']:,.1f}%)", "size": "sm", "flex": 5, "align": "end", "color": profit_color}
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
                            "label": "買い戻す",
                            "data": f"action=stock_detail&symbol={s['symbol_code']}"
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
        alt_text="空売り建玉一覧",
        contents={"type": "carousel", "contents": bubbles}
    )
