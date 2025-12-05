"""
リッチメニューモジュール

LINE Botのリッチメニュー管理機能
"""
from .menu_manager import (
    create_rich_menus,
    delete_all_rich_menus,
    set_default_rich_menu,
    switch_user_menu
)

__all__ = [
    'create_rich_menus',
    'delete_all_rich_menus',
    'set_default_rich_menu',
    'switch_user_menu'
]
