"""
労働システムのFlexMessage生成
"""
from linebot.models import FlexSendMessage


def _create_info_row(label: str, value: str):
    """情報行を作成"""
    return {
        "type": "box",
        "layout": "baseline",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#999999", "flex": 3},
            {"type": "text", "text": value, "size": "sm", "color": "#333333", "flex": 5, "wrap": True, "align": "end"}
        ],
        "spacing": "sm"
    }


def get_salary_account_registration_flex(accounts: list) -> FlexSendMessage:
    """給与振込口座登録 - 口座選択方式"""
    if len(accounts) == 1:
        # 口座が1つの場合
        account = accounts[0]
        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "💼 給与振込口座登録", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#2196F3",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "以下の銀行口座を給与振込用に登録します", "wrap": True, "color": "#666666", "size": "sm"},
                    {"type": "box", "layout": "vertical", "contents": [
                        {"type": "text", "text": "⚠️ 注意", "weight": "bold", "size": "xs", "color": "#FF5722"},
                        {"type": "text", "text": "一度登録すると後から変更できません", "size": "xxs", "color": "#FF5722", "wrap": True}
                    ], "backgroundColor": "#FFEBEE", "paddingAll": "8px", "cornerRadius": "md", "margin": "md"},
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            _create_info_row("名義", account.get('full_name', 'N/A')),
                            _create_info_row("種別", account.get('type', 'N/A')),
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
                            "label": "この口座を登録",
                            "data": f"action=confirm_work_salary_account&account_id={account['account_id']}"
                        },
                        "style": "primary",
                        "color": "#2196F3"
                    }
                ],
                "paddingAll": "15px"
            }
        }
    else:
        # 口座が複数の場合
        account_boxes = []
        for i, acc in enumerate(accounts):
            if i > 0:
                account_boxes.append({"type": "separator", "margin": "lg"})
            account_boxes.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"📌 {acc.get('full_name', 'N/A')}", "size": "md", "weight": "bold", "color": "#2196F3"},
                    {"type": "text", "text": f"種別: {acc.get('type', 'N/A')}", "size": "xs", "color": "#666666", "margin": "sm"},
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
                    "data": f"action=select_work_salary_account&account_id={acc['account_id']}"
                }
            })

        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "💼 口座選択", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#2196F3",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "給与振込用の口座を選択してください", "wrap": True, "color": "#666666", "size": "sm"},
                    {"type": "box", "layout": "vertical", "contents": [
                        {"type": "text", "text": "⚠️ 注意", "weight": "bold", "size": "xs", "color": "#FF5722"},
                        {"type": "text", "text": "一度登録すると後から変更できません", "size": "xxs", "color": "#FF5722", "wrap": True}
                    ], "backgroundColor": "#FFEBEE", "paddingAll": "8px", "cornerRadius": "md", "margin": "md"}
                ] + account_boxes,
                "paddingAll": "20px"
            }
        }

    return FlexSendMessage(alt_text="給与振込口座登録", contents=bubble)
