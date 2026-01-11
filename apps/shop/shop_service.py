"""
ショップ機能サービス
"""
from decimal import Decimal
from sqlalchemy import select
from typing import List, Dict, Optional
from apps.utilities.timezone_utils import now_jst
import datetime
import json

from apps.banking.main_bank_system import (
    SessionLocal,
    Account,
    Branch,
    ShopItem,
    ShopItemAttribute,
    ShopPaymentAccount,
    ShopPurchase,
)

# ショップ運営口座（事前に作成が必要）
SHOP_OPERATIONS_ACCOUNT = {
    "full_name": "ｼｮｯﾌﾟ ｳﾝｴｲ",
    "display_name": "🅺🅸🅼🆄🆁🅰",
    "branch_num": "001",
    "account_number": "2103737",
    "account_type": "当座",
}


def get_shop_operations_account() -> dict:
    """ショップ運営口座情報を取得"""
    return SHOP_OPERATIONS_ACCOUNT


def get_shop_categories() -> List[Dict]:
    """ショップのカテゴリ一覧を取得"""
    return [
        {
            'code': 'casino_chips',
            'name': '🎰 カジノチップ',
            'description': 'ミニゲームで使えるチップ',
            'icon': '🎰'
        },
        {
            'code': 'special_items',
            'name': '✨ 特別アイテム',
            'description': '限定アイテム（準備中）',
            'icon': '✨'
        },
        {
            'code': 'boosters',
            'name': '🚀 ブースター',
            'description': 'ゲームを有利に（準備中）',
            'icon': '🚀'
        }
    ]


def get_items_by_category(category: str) -> List[Dict]:
    """カテゴリ別の商品一覧を取得（属性付き）"""
    db = SessionLocal()
    try:
        items = db.execute(
            select(ShopItem)
            .filter_by(category=category, is_available=True)
            .order_by(ShopItem.display_order)
        ).scalars().all()

        result = []
        for item in items:
            # 商品の属性を取得
            attributes = db.execute(
                select(ShopItemAttribute)
                .filter_by(item_id=item.item_id)
            ).scalars().all()

            # 属性を辞書化
            attrs_dict = {}
            for attr in attributes:
                value = attr.attribute_value

                # 型変換
                if attr.attribute_type == 'integer':
                    value = int(value)
                elif attr.attribute_type == 'decimal':
                    value = float(value)
                elif attr.attribute_type == 'boolean':
                    value = value.lower() in ('true', '1', 'yes')
                elif attr.attribute_type == 'json':
                    value = json.loads(value)

                attrs_dict[attr.attribute_key] = value

            result.append({
                'item_id': item.item_id,
                'item_code': item.item_code,
                'name': item.name,
                'description': item.description,
                'price': int(item.price),
                'attributes': attrs_dict
            })

        return result
    finally:
        db.close()


def get_item_attribute(item_id: int, attribute_key: str, default=None):
    """特定の商品属性を取得"""
    db = SessionLocal()
    try:
        attr = db.execute(
            select(ShopItemAttribute)
            .filter_by(item_id=item_id, attribute_key=attribute_key)
        ).scalars().first()

        if not attr:
            return default

        value = attr.attribute_value

        # 型変換
        if attr.attribute_type == 'integer':
            return int(value)
        elif attr.attribute_type == 'decimal':
            return Decimal(value)
        elif attr.attribute_type == 'boolean':
            return value.lower() in ('true', '1', 'yes')
        elif attr.attribute_type == 'json':
            return json.loads(value)

        return value
    finally:
        db.close()


def register_payment_account(user_id: str, full_name: str, branch_code: str,
                            account_number: str, pin_code: str) -> Dict:
    """
    ショップ支払い用口座を登録
    """
    from apps.banking.bank_service import authenticate_customer

    db = SessionLocal()
    try:
        # 認証
        if not authenticate_customer(full_name, pin_code, branch_code, account_number):
            return {'success': False, 'error': '認証に失敗しました'}

        with db.begin():
            # 支店・口座を取得
            branch = db.execute(select(Branch).filter_by(code=branch_code)).scalars().first()
            if not branch:
                return {'success': False, 'error': '支店が見つかりません'}

            account = db.execute(
                select(Account).filter_by(account_number=account_number, branch_id=branch.branch_id)
            ).scalars().first()

            if not account:
                return {'success': False, 'error': '口座が見つかりません'}

            # ステータスチェック: activeまたはfrozenのみ有効
            if account.status not in ('active', 'frozen'):
                return {'success': False, 'error': 'この口座は利用できません（閉鎖済みまたは無効）'}

            # 口座のユーザーIDチェック
            if account.user_id != user_id:
                return {'success': False, 'error': 'この口座はあなたの口座ではありません'}

            # 既存登録をチェック
            existing = db.execute(
                select(ShopPaymentAccount).filter_by(user_id=user_id)
            ).scalars().first()

            if existing:
                # 更新
                existing.account_id = account.account_id
                existing.is_active = True
                existing.registered_at = now_jst()
                message = 'ショップ支払い用口座を更新しました'
            else:
                # 新規登録
                payment_acc = ShopPaymentAccount(
                    user_id=user_id,
                    account_id=account.account_id,
                    registered_at=now_jst(),
                    is_active=True
                )
                db.add(payment_acc)
                message = 'ショップ支払い用口座を登録しました'

            db.flush()

        return {'success': True, 'message': message}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def register_payment_account_by_id(user_id: str, account_id: int) -> Dict:
    """
    account_idで直接ショップ支払い用口座を登録（株式口座と同じ方式）
    """
    db = SessionLocal()
    try:
        with db.begin():
            # 口座の存在確認とユーザーIDチェック
            account = db.execute(
                select(Account).filter_by(account_id=account_id)
            ).scalars().first()

            if not account:
                return {'success': False, 'error': '口座が見つかりません'}

            # ステータスチェック: activeまたはfrozenのみ有効
            if account.status not in ('active', 'frozen'):
                return {'success': False, 'error': 'この口座は利用できません（閉鎖済みまたは無効）'}

            if account.user_id != user_id:
                return {'success': False, 'error': 'この口座はあなたの口座ではありません'}

            # 既存登録をチェック
            existing = db.execute(
                select(ShopPaymentAccount).filter_by(user_id=user_id)
            ).scalars().first()

            if existing:
                # 更新
                existing.account_id = account.account_id
                existing.is_active = True
                existing.registered_at = now_jst()
                message = 'ショップ支払い用口座を更新しました'
            else:
                # 新規登録
                payment_acc = ShopPaymentAccount(
                    user_id=user_id,
                    account_id=account.account_id,
                    registered_at=now_jst(),
                    is_active=True
                )
                db.add(payment_acc)
                message = 'ショップ支払い用口座を登録しました'

            db.flush()

        return {'success': True, 'message': message}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_payment_account_info(user_id: str) -> Optional[Dict]:
    """ショップ支払い用口座情報を取得"""
    db = SessionLocal()
    try:
        payment_acc = db.execute(
            select(ShopPaymentAccount).filter_by(user_id=user_id, is_active=True)
        ).scalars().first()

        if not payment_acc:
            return None

        account = db.execute(
            select(Account).filter_by(account_id=payment_acc.account_id)
        ).scalars().first()

        if not account:
            return None

        # ステータスチェック: activeまたはfrozenのみ有効
        if account.status not in ('active', 'frozen'):
            return None

        branch_code = account.branch.code if account.branch else None

        return {
            'account_number': account.account_number,
            'branch_code': branch_code,
            'balance': str(account.balance)
        }
    finally:
        db.close()


def purchase_item(user_id: str, item_id: int) -> Dict:
    """商品を購入（正しいフロー: 銀行APIで振込 → チップ付与）"""
    db = SessionLocal()

    try:
        # 商品情報を取得
        item = db.execute(
            select(ShopItem).filter_by(item_id=item_id, is_available=True)
        ).scalars().first()

        if not item:
            return {'success': False, 'error': '商品が見つかりません'}

        # 支払い口座を取得
        payment_info = get_payment_account_info(user_id)
        if not payment_info:
            return {'success': False, 'error': 'payment_account_not_registered'}

        # カテゴリ別の処理
        if item.category == 'casino_chips':
            return _purchase_chip_item(db, user_id, item, payment_info)
        elif item.category == 'gacha_tokens':
            return _purchase_gacha_token(db, user_id, item, payment_info)
        elif item.category == 'special_items':
            return _purchase_special_item(db, user_id, item, payment_info)
        elif item.category == 'boosters':
            return _purchase_booster_item(db, user_id, item, payment_info)

        return {'success': False, 'error': 'この商品カテゴリは現在対応していません'}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def _purchase_chip_item(db, user_id: str, item, payment_info: Dict) -> Dict:
    """チップ商品の購入処理"""
    from apps.banking.chip_service import purchase_chips

    # 属性から数値を取得
    chip_amount = get_item_attribute(item.item_id, 'chip_amount', 0)
    bonus_chip = get_item_attribute(item.item_id, 'bonus_chip', 0)
    total_chips = chip_amount + bonus_chip

    if total_chips <= 0:
        return {'success': False, 'error': '商品設定エラー: チップ数が不正です'}

    # チップ購入実行（ボーナス廃止: bonus分も含めて単一チップとして付与）
    result = purchase_chips(
        user_id=user_id,
        base_amount=total_chips,
        bonus_amount=0,
        account_number=payment_info['account_number'],
        branch_code=payment_info['branch_code'],
        price=item.price
    )

    if not result['success']:
        return result

    _record_purchase(db, user_id, item)

    return {
        'success': True,
        'item_name': item.name,
        'chips_received': total_chips,
        'new_base_balance': result['new_base_balance'],
        'new_bonus_balance': 0
    }


def _purchase_gacha_token(db, user_id: str, item, payment_info: Dict) -> Dict:
    """ガチャトークンの購入処理"""
    from apps.inventory.inventory_service import inventory_service
    from apps.banking.api import banking_api

    token_card_id = get_item_attribute(item.item_id, 'token_card_id')
    amount = get_item_attribute(item.item_id, 'amount', 1)

    if not token_card_id:
        return {'success': False, 'error': '商品設定エラー: トークンIDが未設定です'}

    # 1. 銀行振込（支払い）
    try:
        banking_api.transfer(
            from_account_number=payment_info['account_number'],
            to_account_number=SHOP_OPERATIONS_ACCOUNT['account_number'], # 運営口座へ
            amount=float(item.price),
            currency='JPY',
            description=f"ショップ購入: {item.name}"
        )
    except Exception as e:
        return {'success': False, 'error': f"支払い失敗: {str(e)}"}

    # 2. インベントリに追加
    inventory_service.add_item(user_id, token_card_id, amount)

    # 3. 履歴記録
    _record_purchase(db, user_id, item)

    return {
        'success': True,
        'item_name': item.name,
        'amount': amount
    }


def _record_purchase(db, user_id, item):
    try:
        with db.begin_nested():
            purchase = ShopPurchase(
                user_id=user_id,
                item_id=item.item_id,
                quantity=1,
                total_price=item.price,
                status='completed'
            )
            db.add(purchase)
            db.flush()
    except Exception as e:
        print(f"[Shop] Failed to record purchase history: {e}")


def _purchase_special_item(db, user_id: str, item, payment_info: Dict) -> Dict:
    """特別アイテムの購入処理（将来実装）"""
    return {'success': False, 'error': '特別アイテムは現在準備中です'}


def _purchase_booster_item(db, user_id: str, item, payment_info: Dict) -> Dict:
    """ブースターの購入処理（将来実装）"""
    return {'success': False, 'error': 'ブースターは現在準備中です'}
