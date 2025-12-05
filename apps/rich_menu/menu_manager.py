"""
リッチメニュー管理

LINE Messaging APIを使用したリッチメニューのCRUD操作
"""
import os
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds
from linebot.models.actions import PostbackAction
from config import LINE_CHANNEL_ACCESS_TOKEN
from .menu_templates import get_all_templates


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
        action = PostbackAction(
            data=area_def["action"]["data"],
            display_text=area_def["action"].get("displayText", "")
        )
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
