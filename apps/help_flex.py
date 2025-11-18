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
                        {"type": "text", "text": "ページ 1/3", "size": "xs", "color": "#999999", "align": "center"}
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
                        {"type": "text", "text": "ページ 2/3", "size": "xs", "color": "#999999", "align": "center"}
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
                        {"type": "text", "text": "ページ 3/3", "size": "xs", "color": "#999999", "align": "center"}
                    ],
                    "paddingAll": "10px"
                }
            }
        ]
    }
    return FlexSendMessage(alt_text="コマンドヘルプ", contents=help_carousel)
