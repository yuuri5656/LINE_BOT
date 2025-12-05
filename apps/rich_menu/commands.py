"""
リッチメニュー管理コマンド

リッチメニューの作成・更新・削除などの管理操作
"""
from linebot.models import TextSendMessage
from core.api import line_bot_api
from .menu_manager import (
    create_rich_menus,
    delete_all_rich_menus,
    set_default_rich_menu,
    get_menu_ids
)


def handle_menu_create(event):
    """リッチメニューを作成"""
    try:
        # 既存のメニューを削除
        delete_all_rich_menus()
        
        # 新しいメニューを作成
        menu_ids = create_rich_menus()
        
        # デフォルトメニューを設定（ページ1-1）
        set_default_rich_menu(page="1-1")
        
        message = TextSendMessage(
            text=f"✅ リッチメニューを作成しました\n\n"
                 f"📄 ページ1-1: {menu_ids['page1-1'][:8]}...\n"
                 f"📄 ページ1-2: {menu_ids['page1-2'][:8]}...\n"
                 f"📄 ページ1-3: {menu_ids['page1-3'][:8]}...\n"
                 f"📄 ページ2-1: {menu_ids['page2-1'][:8]}...\n"
                 f"📄 ページ2-2: {menu_ids['page2-2'][:8]}...\n"
                 f"📄 ページ2-3: {menu_ids['page2-3'][:8]}...\n\n"
                 f"メニューが表示されない場合は、トーク画面を再読み込みしてください。"
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        error_message = TextSendMessage(
            text=f"❌ エラーが発生しました\n{str(e)}\n\n"
                 f"画像ファイルが apps/rich_menu/images/ に配置されているか確認してください。"
        )
        line_bot_api.reply_message(event.reply_token, error_message)


def handle_menu_delete(event):
    """リッチメニューを削除"""
    try:
        delete_all_rich_menus()
        message = TextSendMessage(text="✅ 全てのリッチメニューを削除しました")
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        error_message = TextSendMessage(text=f"❌ エラーが発生しました\n{str(e)}")
        line_bot_api.reply_message(event.reply_token, error_message)


def handle_menu_status(event):
    """リッチメニューの状態を表示"""
    try:
        menu_ids = get_menu_ids()
        
        any_menu_exists = any(menu_ids.values())
        
        if any_menu_exists:
            status_text = "📊 リッチメニュー状態\n\n"
            for page_key in ["page1-1", "page1-2", "page1-3", "page2-1", "page2-2", "page2-3"]:
                if menu_ids[page_key]:
                    status_text += f"✅ {page_key}: {menu_ids[page_key][:8]}...\n"
                else:
                    status_text += f"❌ {page_key}: 未作成\n"
        else:
            status_text = "❌ リッチメニューが作成されていません\n\n?メニュー作成 で作成できます。"
        
        message = TextSendMessage(text=status_text)
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        error_message = TextSendMessage(text=f"❌ エラーが発生しました\n{str(e)}")
        line_bot_api.reply_message(event.reply_token, error_message)
