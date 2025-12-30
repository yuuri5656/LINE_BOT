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
             "action": {"type": "postback", "data": "action=help_detail_account"}},
            # ページ1-1へ遷移（無視）
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-1", "data": "action=richmenu_switched&page=1-1"}},
            # ページ1-2へ遷移
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-2", "data": "action=richmenu_switched&page=1-2"}},
            # ページ1-3へ遷移
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # 口座開設
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=account_create"}},
            # 通帳
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=passbook"}},
            # 振り込み
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=transfer"}}
        ]
    }


def get_page1_2_template():
    """ページ1-2: ショップ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "ショップメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ショップ機能）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_shop"}},
            # ページ1-1へ遷移
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-1", "data": "action=richmenu_switched&page=1-1"}},
            # ページ1-2へ遷移（無視）
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-2", "data": "action=richmenu_switched&page=1-2"}},
            # ページ1-3へ遷移
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # ショップ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=shop_home"}},
            # チップ残高
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_balance"}},
            # チップ換金
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_exchange"}}
        ]
    }


def get_page1_3_template():
    """ページ1-3: 株式システム"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "株式システムメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（株式システム）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_stock"}},
            # ページ1-1へ遷移
            {"bounds": {"x": 50, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-1", "data": "action=richmenu_switched&page=1-1"}},
            # ページ1-2へ遷移
            {"bounds": {"x": 760, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-2", "data": "action=richmenu_switched&page=1-2"}},
            # ページ1-3へ遷移（無視）
            {"bounds": {"x": 1470, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 2180, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # 株式ダッシュボード
            {"bounds": {"x": 115, "y": 624, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=stock_home"}},
            # 銘柄一覧
            {"bounds": {"x": 1285, "y": 624, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=stock_list"}},
            # 保有株一覧
            {"bounds": {"x": 115, "y": 1150, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=my_holdings"}},
            # 市場ニュース
            {"bounds": {"x": 1285, "y": 1150, "width": 1100, "height": 400},
             "action": {"type": "postback", "data": "action=market_news"}}
        ]
    }


def get_page2_1_template():
    """ページ2-1: ゲーム"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "ゲームメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ゲーム）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_game"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移（無視）
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # ページ2-2へ遷移
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-2", "data": "action=richmenu_switched&page=2-2"}},
            # ページ2-3へ遷移
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-3", "data": "action=richmenu_switched&page=2-3"}},
            # ゲームメニュー
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=game_home"}},
            # チップ一覧（ショップ）
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_list"}},
            # チップ換金
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=chip_exchange"}}
        ]
    }


def get_page2_2_template():
    """ページ2-2: ユーティリティ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "ユーティリティメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ユーティリティ）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_detail_utility"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # ページ2-2へ遷移（無視）
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-2", "data": "action=richmenu_switched&page=2-2"}},
            # ページ2-3へ遷移
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-3", "data": "action=richmenu_switched&page=2-3"}},
            # おみくじ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=omikuji"}},
            # 明日の時間割
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=timetable"}},
            # 労働
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=work_home"}}
        ]
    }


def get_page2_3_template():
    """ページ2-3: ヘルプ"""
    return {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "ヘルプメニュー",
        "chatBarText": "メニュー",
        "areas": [
            # 詳細ヘルプ（ヘルプ本体）
            {"bounds": {"x": 350, "y": 0, "width": 1800, "height": 190},
             "action": {"type": "postback", "data": "action=help_home"}},
            # ページ1-3へ遷移（前ページへ）
            {"bounds": {"x": 50, "y": 190, "width": 270, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page1-3", "data": "action=richmenu_switched&page=1-3"}},
            # ページ2-1へ遷移
            {"bounds": {"x": 350, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-1", "data": "action=richmenu_switched&page=2-1"}},
            # ページ2-2へ遷移
            {"bounds": {"x": 1060, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-2", "data": "action=richmenu_switched&page=2-2"}},
            # ページ2-3へ遷移（無視）
            {"bounds": {"x": 1770, "y": 190, "width": 680, "height": 230},
             "action": {"type": "richmenuswitch", "richMenuAliasId": "rm_page2-3", "data": "action=richmenu_switched&page=2-3"}},
            # ヘルプ
            {"bounds": {"x": 168, "y": 563, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_home"}},
            # 口座関連の詳細ヘルプ
            {"bounds": {"x": 168, "y": 924, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_detail_account"}},
            # 株式システムの詳細ヘルプ
            {"bounds": {"x": 168, "y": 1285, "width": 2160, "height": 295},
             "action": {"type": "postback", "data": "action=help_detail_stock"}}
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
