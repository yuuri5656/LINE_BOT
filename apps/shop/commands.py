"""
ショップコマンドとpostbackハンドラー
"""
from linebot.models import TextSendMessage
from apps.shop.session_manager import shop_session_manager
from apps.banking.chip_service import get_chip_balance, get_chip_history, redeem_chips
from apps.shop import shop_service, shop_flex
from typing import Optional


def handle_shop_command(user_id: str, db):
    """?ショップコマンド"""
    categories = shop_service.get_shop_categories()
    return shop_flex.get_shop_home_carousel(categories)


def handle_chip_balance_command(user_id: str, db):
    """?チップ残高コマンド"""
    balance_info = get_chip_balance(user_id)
    balance = balance_info.get('balance', 0)
    locked = balance_info.get('locked', 0)
    available = balance_info.get('available', 0)

    if locked > 0:
        return TextSendMessage(
            text=f"💰 チップ残高\n"
                 f"総額: {balance}枚\n"
                 f"ロック中: {locked}枚\n"
                 f"利用可能: {available}枚"
        )
    else:
        return TextSendMessage(text=f"💰 現在のチップ残高: {balance}枚")


def handle_chip_redeem_command(user_id: str, text: str, db):
    """?チップ換金コマンド"""
    # コマンドパース: ?チップ換金 100
    parts = text.strip().split()

    if len(parts) == 1:
        # 枚数指定なし: 利用方法を表示
        return TextSendMessage(
            text="💵 チップ換金\n\n"
                 "使用方法: ?チップ換金 <枚数>\n"
                 "例: ?チップ換金 100\n\n"
                 "換金率: 1チップ = 1 JPY (100%)\n"
                 "※登録済みの支払い口座に振り込まれます"
        )

    try:
        amount = int(parts[1])
    except (ValueError, IndexError):
        return TextSendMessage(text="❌ 枚数は整数で指定してください。\n例: ?チップ換金 100")

    if amount <= 0:
        return TextSendMessage(text="❌ 1枚以上を指定してください。")

    # 換金実行
    result = redeem_chips(user_id, amount)

    if result['success']:
        return TextSendMessage(
            text=f"✅ チップ換金完了\n\n"
                 f"換金枚数: {result['amount_received']}枚\n"
                 f"振込額: {result['amount_received']} JPY\n"
                 f"残りのチップ: {result['new_balance']}枚\n\n"
                 f"※登録済みの口座に振り込まれました"
        )
    else:
        return TextSendMessage(text=f"❌ 換金に失敗しました\n{result['error']}")


def handle_chip_history_command(user_id: str, db):
    """?チップ履歴コマンド"""
    transactions = get_chip_history(user_id, limit=10)

    if not transactions:
        return TextSendMessage(text="チップの取引履歴がありません。")

    lines = ["📊 チップ取引履歴 (最新10件)\n"]

    for tx in transactions:
        tx_type = tx['type']
        amount = tx['amount']
        timestamp = tx['created_at']

        if tx_type == 'purchase':
            lines.append(f"✅ {timestamp} 購入 +{amount}枚")
        elif tx_type == 'redeem':
            lines.append(f"💵 {timestamp} 換金 {amount}枚")
        elif tx_type == 'game_bet':
            lines.append(f"🎰 {timestamp} ゲーム賭け {amount}枚")
        elif tx_type == 'game_win':
            lines.append(f"🎉 {timestamp} ゲーム勝利 +{amount}枚")
        elif tx_type == 'transfer_out':
            lines.append(f"📤 {timestamp} 送信 {amount}枚")
        elif tx_type == 'transfer_in':
            lines.append(f"📥 {timestamp} 受信 +{amount}枚")
        else:
            lines.append(f"• {timestamp} {tx_type} {amount:+}枚")

    return TextSendMessage(text="\n".join(lines))


def handle_shop_postback(user_id: str, data: dict, db, message_text: Optional[str] = None):
    """
    ショップ関連のpostback処理

    Args:
        user_id: ユーザーID
        data: postbackデータ（パース済み）
        db: データベースセッション
        message_text: ユーザーが送信したテキスト（セッション中のメッセージ）
    """
    action = data.get('action')

    # ショップホーム表示
    if action == 'shop_home':
        return handle_shop_command(user_id, db)

    # カテゴリ選択
    elif action == 'shop_category':
        category = data.get('category')
        items = shop_service.get_items_by_category(category)

        category_names = {
            'casino_chips': 'カジノチップ',
            'special_items': 'スペシャルアイテム',
            'boosters': 'ブースター'
        }
        category_name = category_names.get(category, category)

        return shop_flex.get_category_items_flex(category_name, items)

    # 商品購入
    elif action == 'shop_buy':
        item_id = int(data.get('item_id'))

        # 支払い口座の登録確認
        payment_info = shop_service.get_payment_account_info(user_id)

        if not payment_info:
            # 未登録の場合、登録案内を表示
            return shop_flex.get_payment_account_registration_flex()

        # 購入実行
        try:
            result = shop_service.purchase_item(user_id, item_id)

            if result['success']:
                return shop_flex.get_purchase_success_flex(
                    item_name=result['item_name'],
                    chips_received=result['chips_received'],
                    new_balance=result['new_balance']
                )
            else:
                return TextSendMessage(text=f"❌ 購入に失敗しました: {result['message']}")

        except Exception as e:
            return TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")

    # 支払い口座登録開始
    elif action == 'register_payment_account':
        shop_session_manager.start_session(user_id, {
            'type': 'payment_registration',
            'step': 'branch_code'
        })
        return TextSendMessage(text="支店番号（3桁）を入力してください。")

    # セッション中のメッセージ処理
    elif message_text is not None:
        return handle_payment_registration_session(user_id, message_text, db)

    return None


def handle_payment_registration_session(user_id: str, message_text: str, db):
    """支払い口座登録セッション処理"""
    session = shop_session_manager.get_session(user_id)

    if not session or session['type'] != 'payment_registration':
        return None

    step = session['step']

    # ステップ1: 支店番号
    if step == 'branch_code':
        if not message_text.isdigit() or len(message_text) != 3:
            return TextSendMessage(text="❌ 支店番号は3桁の数字で入力してください。")

        session['branch_code'] = message_text
        session['step'] = 'account_number'
        shop_session_manager.update_session(user_id, session)

        return TextSendMessage(text="口座番号（7桁）を入力してください。")

    # ステップ2: 口座番号
    elif step == 'account_number':
        if not message_text.isdigit() or len(message_text) != 7:
            return TextSendMessage(text="❌ 口座番号は7桁の数字で入力してください。")

        session['account_number'] = message_text
        session['step'] = 'account_name'
        shop_session_manager.update_session(user_id, session)

        return TextSendMessage(text="口座名義（半角カナ）を入力してください。\n例: ﾔﾏﾀﾞ ﾀﾛｳ")

    # ステップ3: 口座名義
    elif step == 'account_name':
        import re
        account_name = message_text.strip()

        # 全角カタカナが含まれている場合は半角カナに変換
        has_zen_kana = re.search(r'[ァ-ンヴー]', account_name)
        if has_zen_kana:
            try:
                import jaconv
                account_name = jaconv.z2h(account_name, kana=True, digit=False, ascii=False)
            except ImportError:
                return TextSendMessage(text="❌ 全角カナが含まれていますが、変換に失敗しました。半角カナで入力してください。")

        # 半角カナのみを許可
        is_hankaku_kana = re.match(r'^[ｦ-ﾟ\s]+$', account_name)
        if not is_hankaku_kana:
            return TextSendMessage(text="❌ 口座名義は半角カナで入力してください。\n例: ﾔﾏﾀﾞ ﾀﾛｳ")

        session['account_name'] = account_name
        session['step'] = 'pin_code'
        shop_session_manager.update_session(user_id, session)

        return TextSendMessage(text="最後に、暗証番号（4桁）を入力してください。")

    # ステップ4: 暗証番号（登録実行）
    elif step == 'pin_code':
        if not message_text.isdigit() or len(message_text) != 4:
            return TextSendMessage(text="❌ 暗証番号は4桁の数字で入力してください。")

        # 口座登録を実行
        try:
            result = shop_service.register_payment_account(
                user_id=user_id,
                full_name=session['account_name'],
                branch_code=session['branch_code'],
                account_number=session['account_number'],
                pin_code=message_text
            )

            shop_session_manager.end_session(user_id)

            if result['success']:
                return TextSendMessage(
                    text=f"✅ 支払い用口座を登録しました！\n\n"
                         f"支店番号: {session['branch_code']}\n"
                         f"口座番号: {session['account_number']}\n"
                         f"名義: {session['account_name']}\n\n"
                         f"ショップでお買い物をお楽しみください！"
                )
            else:
                error_msg = result.get('error', result.get('message', '不明なエラー'))
                return TextSendMessage(text=f"❌ 登録に失敗しました: {error_msg}")

        except Exception as e:
            shop_session_manager.end_session(user_id)
            return TextSendMessage(text=f"❌ エラーが発生しました: {str(e)}")

    return None
