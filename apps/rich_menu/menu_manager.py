"""
リッチメニュー管理

LINE Messaging APIを使用したリッチメニューのCRUD操作
"""
import os
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds
from linebot.models.actions import PostbackAction
from linebot.models.actions import RichMenuSwitchAction
from config import LINE_CHANNEL_ACCESS_TOKEN
from .menu_templates import get_all_templates

import requests


# LINE Bot API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# リッチメニューIDを保存（グローバル変数）
RICHMENU_IDS = {
    "page1-1": None,
    "page1-2": None,
    "page1-3": None,
    "page2-1": None,
    "page2-2": None,
    "page2-3": None
}

# richMenuAliasId（固定）: richmenuswitch が参照する
RICHMENU_ALIASES = {
    # NOTE: richMenuAliasId はドット不可。英小文字/数字/ハイフン/アンダースコアで構成する。
    "page1-1": "rm_page1-1",
    "page1-2": "rm_page1-2",
    "page1-3": "rm_page1-3",
    "page2-1": "rm_page2-1",
    "page2-2": "rm_page2-2",
    "page2-3": "rm_page2-3",
}


def _line_api_headers() -> dict:
    return {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def ensure_rich_menu_alias(alias_id: str, rich_menu_id: str) -> bool:
    """rich menu alias を作成（既にあれば更新）する。

    line-bot-sdk には alias API が無いので、Messaging API を直接呼ぶ。
    """
    if not alias_id or not rich_menu_id:
        return False

    base = "https://api.line.me/v2/bot/richmenu/alias"
    timeout_seconds = 8

    # まず作成を試行（存在する場合は更新へフォールバック）
    try:
        resp = requests.post(
            base,
            headers=_line_api_headers(),
            json={"richMenuAliasId": alias_id, "richMenuId": rich_menu_id},
            timeout=timeout_seconds,
        )
        if resp.status_code in (200, 201):
            print(f"[リッチメニュー] alias作成: {alias_id} -> {rich_menu_id}")
            return True

        # 既存aliasの可能性（409 / 400）
        if resp.status_code not in (400, 409):
            print(f"[リッチメニュー] alias作成失敗: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[リッチメニュー] alias作成例外: {e}")

    # 更新（aliasが既に存在する前提）
    try:
        resp = requests.post(
            f"{base}/{alias_id}",
            headers=_line_api_headers(),
            json={"richMenuId": rich_menu_id},
            timeout=timeout_seconds,
        )
        if resp.status_code in (200, 201):
            print(f"[リッチメニュー] alias更新: {alias_id} -> {rich_menu_id}")
            return True
        print(f"[リッチメニュー] alias更新失敗: {resp.status_code} - {resp.text}")
        return False
    except Exception as e:
        print(f"[リッチメニュー] alias更新例外: {e}")
        return False


def create_rich_menu(template: dict, image_path: str) -> str:
    """
    リッチメニューを作成
    
    Args:
        template: メニューテンプレート（menu_templates.pyから取得）
        image_path: メニュー画像のパス（2500x1686px）
    
    Returns:
        作成されたリッチメニューのID
    """
    # RichMenuオブジェクト作成
    areas = []
    for area_def in template["areas"]:
        bounds = RichMenuBounds(
            x=area_def["bounds"]["x"],
            y=area_def["bounds"]["y"],
            width=area_def["bounds"]["width"],
            height=area_def["bounds"]["height"]
        )
        action_def = area_def["action"]
        action_type = action_def.get("type")

        if action_type == "richmenuswitch":
            # LINE側でのメニュー切替。必要ならdataでpostbackを飛ばせる。
            alias_id = action_def.get("richMenuAliasId")
            data = action_def.get("data")
            action = RichMenuSwitchAction(rich_menu_alias_id=alias_id, data=data)
        else:
            # displayTextがある場合のみ設定（メッセージ送信を防ぐ）
            action_params = {"data": action_def["data"]}
            if "displayText" in action_def and action_def["displayText"]:
                action_params["display_text"] = action_def["displayText"]
            action = PostbackAction(**action_params)

        areas.append(RichMenuArea(bounds=bounds, action=action))
    
    rich_menu = RichMenu(
        size=RichMenuSize(
            width=template["size"]["width"],
            height=template["size"]["height"]
        ),
        selected=template["selected"],
        name=template["name"],
        chat_bar_text=template["chatBarText"],
        areas=areas
    )
    
    # 画像の存在チェック
    if not os.path.exists(image_path):
        print(f"[リッチメニュー] エラー: 画像が見つかりません: {image_path}")
        print(f"[リッチメニュー] {template['name']} の作成をスキップします")
        return None
    
    # リッチメニューをLINEサーバーに作成
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)
    
    # 画像をアップロード
    with open(image_path, 'rb') as f:
        line_bot_api.set_rich_menu_image(rich_menu_id, 'image/png', f)
    print(f"[リッチメニュー] 画像をアップロードしました: {image_path}")
    
    print(f"[リッチメニュー] 作成完了: {template['name']} (ID: {rich_menu_id})")
    return rich_menu_id


def create_rich_menus(image_dir: str = "apps/rich_menu/images") -> dict:
    """
    全てのリッチメニューを作成
    
    Args:
        image_dir: 画像ディレクトリのパス
    
    Returns:
        各ページのリッチメニューID
    """
    templates = get_all_templates()
    
    # 画像命名規則: rich_menu_page_(ページ番号-左から数えて何番目か)_(カテゴリ名).png
    menu_configs = [
        ("page1-1", "rich_menu_page_1-1_account.png"),
        ("page1-2", "rich_menu_page_1-2_shop.png"),
        ("page1-3", "rich_menu_page_1-3_stock.png"),
        ("page2-1", "rich_menu_page_2-1_game.png"),
        ("page2-2", "rich_menu_page_2-2_utility.png"),
        ("page2-3", "rich_menu_page_2-3_help.png")
    ]
    
    created_count = 0
    failed_pages = []
    
    for page_key, image_filename in menu_configs:
        image_path = os.path.join(image_dir, image_filename)
        menu_id = create_rich_menu(templates[page_key], image_path)
        RICHMENU_IDS[page_key] = menu_id

        # richmenuswitch 用 alias を作成/更新
        if menu_id:
            alias_id = RICHMENU_ALIASES.get(page_key)
            if alias_id:
                ensure_rich_menu_alias(alias_id=alias_id, rich_menu_id=menu_id)
        
        if menu_id:
            created_count += 1
        else:
            failed_pages.append(page_key)
    
    print(f"[リッチメニュー] 作成結果: {created_count}/6 個のメニューを作成")
    if failed_pages:
        print(f"[リッチメニュー] 作成失敗: {', '.join(failed_pages)}")
    
    return RICHMENU_IDS


def delete_all_rich_menus():
    """全てのリッチメニューを削除"""
    try:
        rich_menu_list = line_bot_api.get_rich_menu_list()
        for menu in rich_menu_list:
            line_bot_api.delete_rich_menu(menu.rich_menu_id)
            print(f"[リッチメニュー] 削除: {menu.name} (ID: {menu.rich_menu_id})")
        
        # グローバル変数をリセット
        for key in RICHMENU_IDS:
            RICHMENU_IDS[key] = None
        
        print("[リッチメニュー] 全てのメニューを削除しました")
    except Exception as e:
        print(f"[リッチメニュー] 削除エラー: {e}")


def set_default_rich_menu(page: str = "1-1"):
    """
    デフォルトのリッチメニューを設定
    
    Args:
        page: デフォルトで表示するページ（例: "1-1", "2-1"）
    """
    page_key = f"page{page}"
    menu_id = RICHMENU_IDS.get(page_key)
    if menu_id:
        try:
            line_bot_api.set_default_rich_menu(menu_id)
            print(f"[リッチメニュー] デフォルトメニューを設定: {page_key} (ID: {menu_id})")
        except Exception as e:
            print(f"[リッチメニュー] デフォルト設定エラー: {e}")
    else:
        print(f"[リッチメニュー] エラー: {page_key}のメニューIDが見つかりません")


def switch_user_menu(user_id: str, page: str):
    """
    ユーザーのリッチメニューを切り替え
    
    Args:
        user_id: ユーザーID
        page: 切り替え先のページ（例: "1-1", "1-2", "2-1"）
    """
    page_key = f"page{page}"
    menu_id = RICHMENU_IDS.get(page_key)
    if menu_id:
        try:
            line_bot_api.link_rich_menu_to_user(user_id, menu_id)
            print(f"[リッチメニュー] ユーザー {user_id} を{page_key}に切り替え")
        except Exception as e:
            print(f"[リッチメニュー] 切り替えエラー: {e}")
    else:
        print(f"[リッチメニュー] エラー: {page_key}のメニューIDが見つかりません")


def get_menu_ids():
    """現在のリッチメニューIDを取得"""
    return RICHMENU_IDS.copy()
