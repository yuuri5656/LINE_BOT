"""
リッチメニューテンプレート定義

各ページのメニュー構造とヒットボックス（タップ領域）を定義

画像構成: 
- ページ1: 1-1(口座管理), 1-2(ショップ), 1-3(株式) の3枚
- ページ2: 2-1(ゲーム), 2-2(ユーティリティ), 2-3(ヘルプ) の3枚

画像サイズ: 2500x1686px
画像命名規則: rich_menu_page_(ページ番号-左から数えて何番目か)_(カテゴリ名).png
"""

def get_page1_1_template():
    """ページ1-1: 口座管理（銀行）"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "口座管理メニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（口座関連）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_account", "displayText": "💡 口座関連のヘルプ"}},
            # ページ1-1へ遷移（無視）
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-1&subpage=1", "displayText": ""}},
            # ページ1-2へ遷移
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-2&subpage=1", "displayText": "🛒 ショップ"}},
            # ページ1-3へ遷移
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": "📈 株式"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": "▶️ 次へ"}},
            # 口座開設
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=account_create", "displayText": "💰 口座開設"}},
            # 通帳
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=passbook", "displayText": "📖 通帳"}},
            # 振り込み
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=transfer", "displayText": "💸 振り込み"}}
        ]
    }


def get_page1_2_template():
    """ページ1-2: ショップ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": False,
        "name": "ショップメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ショップ機能）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_shop", "displayText": "💡 ショップのヘルプ"}},
            # ページ1-1へ遷移
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-1&subpage=1", "displayText": "💰 口座管理"}},
            # ページ1-2へ遷移（無視）
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-2&subpage=1", "displayText": ""}},
            # ページ1-3へ遷移
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": "📈 株式"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": "▶️ 次へ"}},
            # ショップ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=shop_home", "displayText": "🛒 ショップ"}},
            # チップ残高
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_balance", "displayText": "💎 チップ残高"}},
            # チップ換金
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_exchange", "displayText": "💵 チップ換金"}}
        ]
    }


def get_page1_3_template():
    """ページ1-3: 株式システム"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": False,
        "name": "株式システムメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（株式システム）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_stock", "displayText": "💡 株式のヘルプ"}},
            # ページ1-1へ遷移
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-1&subpage=1", "displayText": "💰 口座管理"}},
            # ページ1-2へ遷移
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-2&subpage=1", "displayText": "🛒 ショップ"}},
            # ページ1-3へ遷移（無視）
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": ""}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": "▶️ 次へ"}},
            # 株式ダッシュボード
            {"bounds": {"x": 115, "y": 624, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=stock_home", "displayText": "📊 株式ダッシュボード"}},
            # 銘柄一覧
            {"bounds": {"x": 1285, "y": 624, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=stock_list", "displayText": "📋 銘柄一覧"}},
            # 保有株一覧
            {"bounds": {"x": 115, "y": 1150, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=my_holdings", "displayText": "📈 保有株一覧"}},
            # 市場ニュース
            {"bounds": {"x": 1285, "y": 1150, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=market_news", "displayText": "📰 市場ニュース"}}
        ]
    }


def get_page2_1_template():
    """ページ2-1: ゲーム"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": False,
        "name": "ゲームメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ゲーム）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_game", "displayText": "💡 ゲームのヘルプ"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": "◀️ 前へ"}},
            # ページ2-1へ遷移（無視）
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": ""}},
            # ページ2-2へ遷移
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-2&subpage=2", "displayText": "🛠️ ユーティリティ"}},
            # ページ2-3へ遷移
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-3&subpage=2", "displayText": "❓ ヘルプ"}},
            # ゲームメニュー
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=game_home", "displayText": "🎮 ゲームメニュー"}},
            # チップ一覧（ショップ）
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_list", "displayText": "💎 チップ一覧"}},
            # チップ換金
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_exchange", "displayText": "💵 チップ換金"}}
        ]
    }


def get_page2_2_template():
    """ページ2-2: ユーティリティ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": False,
        "name": "ユーティリティメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ユーティリティ）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_utility", "displayText": "💡 ユーティリティのヘルプ"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": "◀️ 前へ"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": "🎮 ゲーム"}},
            # ページ2-2へ遷移（無視）
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-2&subpage=2", "displayText": ""}},
            # ページ2-3へ遷移
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-3&subpage=2", "displayText": "❓ ヘルプ"}},
            # おみくじ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=omikuji", "displayText": "🔮 おみくじ"}},
            # 明日の時間割
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=timetable", "displayText": "📅 明日の時間割"}},
            # 労働
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=work_home", "displayText": "💼 労働"}}
        ]
    }


def get_page2_3_template():
    """ページ2-3: ヘルプ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": False,
        "name": "ヘルプメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ヘルプ本体）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_home", "displayText": "💡 ヘルプ"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=1-3&subpage=1", "displayText": "◀️ 前へ"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-1&subpage=2", "displayText": "🎮 ゲーム"}},
            # ページ2-2へ遷移
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-2&subpage=2", "displayText": "🛠️ ユーティリティ"}},
            # ページ2-3へ遷移（無視）
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "postback", "data": "action=richmenu_page&page=2-3&subpage=2", "displayText": ""}},
            # ヘルプ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_home", "displayText": "❓ ヘルプ"}},
            # 口座関連の詳細ヘルプ
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_detail_account", "displayText": "💰 口座関連ヘルプ"}},
            # 株式システムの詳細ヘルプ
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_detail_stock", "displayText": "📈 株式システムヘルプ"}}
        ]
    }


def get_all_templates():
    """全てのメニューテンプレートを取得"""
    return {
        "page1-1": get_page1_1_template(),
        "page1-2": get_page1_2_template(),
        "page1-3": get_page1_3_template(),
        "page2-1": get_page2_1_template(),
        "page2-2": get_page2_2_template(),
        "page2-3": get_page2_3_template()
    }
