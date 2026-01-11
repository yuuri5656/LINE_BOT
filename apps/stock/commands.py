"""
株式トレード関連のコマンドハンドラー
"""
from linebot.models import TextSendMessage, FlexSendMessage, ImageSendMessage
from core.api import line_bot_api
from apps.stock.api import stock_api
from apps.stock import stock_flex
from apps.banking.api import banking_api
import urllib.parse


def handle_stock_command(event, user_id):
    """?株 コマンド - ダッシュボード表示"""
    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    # 株式口座の有無を確認
    stock_account = stock_api.get_stock_account(user_id)

    if not stock_account:
        # 口座未登録 - 登録フローを開始
        handle_account_registration(event, user_id)
        return

    # ダッシュボード表示
    dashboard = stock_flex.get_stock_dashboard(user_id, has_account=True)
    line_bot_api.reply_message(event.reply_token, dashboard)


def handle_account_registration(event, user_id):
    """株式口座登録フロー開始"""
    # 銀行口座を取得
    bank_accounts = banking_api.get_accounts_by_user(user_id)

    if not bank_accounts or len(bank_accounts) == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="銀行口座が見つかりません。先に「?口座開設」で銀行口座を作成してください。")
        )
        return

    # FlexMessage用に名前をマッピング
    for acc in bank_accounts:
        acc['account_holder'] = acc.get('full_name', 'N/A')
        acc['account_type'] = acc.get('type', 'N/A')

    # 株式口座登録セッション開始
    stock_api.start_account_registration_session(user_id, bank_accounts)

    # 登録FlexMessage表示
    registration_flex = stock_flex.get_account_registration_flex(bank_accounts)
    line_bot_api.reply_message(event.reply_token, registration_flex)


def handle_stock_list(event, user_id):
    """銘柄一覧表示"""
    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    stocks = stock_api.get_all_stocks()

    if not stocks:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="銘柄情報を取得できませんでした。")
        )
        return

    # カルーセル表示
    carousel = stock_flex.get_stock_list_carousel(stocks, page=0, per_page=10)
    line_bot_api.reply_message(event.reply_token, carousel)


def handle_stock_detail(event, symbol_code: str, user_id: str):
    """銘柄詳細表示"""
    # ローディングアニメーション表示（チャート生成に時間がかかるため）
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=30)

    stock = stock_api.get_stock_by_code(symbol_code)

    if not stock:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="指定された銘柄が見つかりません。")
        )
        return

    # 保有株チェック
    holdings = stock_api.get_user_holdings(user_id)
    has_holding = any(h['symbol_code'] == symbol_code for h in holdings)

    # 空売りチェック
    shorts = stock_api.get_short_positions(user_id)
    has_short = any(s['symbol_code'] == symbol_code for s in shorts)

    # 詳細FlexMessage
    detail_flex = stock_flex.get_stock_detail_flex(stock, has_holding, has_short)

    # チャート画像生成（1週間分: 2016ポイント → 自動間引きで約400ポイントに削減）
    chart_url = stock_api.generate_stock_chart(symbol_code, days=2016)

    messages = [detail_flex]

    if chart_url:
        # 画像URLを使ってImageSendMessageで送信
        from linebot.models import ImageSendMessage
        chart_image = ImageSendMessage(
            original_content_url=chart_url,
            preview_image_url=chart_url
        )
        messages.append(chart_image)

    line_bot_api.reply_message(event.reply_token, messages)
def handle_my_holdings(event, user_id: str):
    """保有株一覧表示"""
    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    holdings = stock_api.get_user_holdings(user_id)

    if not holdings or len(holdings) == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="現在、保有している株式はありません。")
        )
        return

    # 保有株カルーセル
    carousel = stock_flex.get_holdings_carousel(holdings)
    line_bot_api.reply_message(event.reply_token, carousel)


def handle_my_short_positions(event, user_id: str):
    """空売り建玉一覧表示"""
    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    shorts = stock_api.get_short_positions(user_id)

    if not shorts or len(shorts) == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="現在、空売りポジションはありません。")
        )
        return

    # 空売りカルーセル
    carousel = stock_flex.get_short_positions_carousel(shorts)
    line_bot_api.reply_message(event.reply_token, carousel)


def handle_market_news(event):
    """市場ニュース（イベント）表示"""
    events = stock_api.get_recent_events(limit=10)

    if not events:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="最近のイベント情報はありません。")
        )
        return

    # イベント情報をテキストで表示
    text = "📰 最近の経済ニュース\n\n"
    for e in events[:5]:
        text += f"• {e['event_text']}\n"
        text += f"  {e['name']} ({e['symbol_code']})\n"
        text += f"  影響: {'+' if e['impact'] > 0 else ''}{e['impact']*100:.1f}%\n\n"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))


def handle_buy_stock_start(event, symbol_code: str, user_id: str):
    """株式購入開始"""
    # 個別チャットのみ
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="株式の購入は個別チャットでのみ可能です。")
        )
        return

    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    # 銘柄確認
    stock = stock_api.get_stock_by_code(symbol_code)
    if not stock:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="指定された銘柄が見つかりません。")
        )
        return

    # セッション開始
    stock_api.start_trade_session(user_id, 'buy', symbol_code)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{stock['name']} ({symbol_code})\n現在価格: ¥{stock['current_price']:,}\n\n購入する株数を入力してください。")
    )


def handle_sell_stock_start(event, symbol_code: str, user_id: str):
    """株式売却開始"""
    # 個別チャットのみ
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="株式の売却は個別チャットでのみ可能です。")
        )
        return

    # ローディングアニメーション表示
    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    # 保有株確認
    holdings = stock_api.get_user_holdings(user_id)
    holding = next((h for h in holdings if h['symbol_code'] == symbol_code), None)

    if not holding:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="この銘柄を保有していません。")
        )
        return

    # セッション開始
    stock_api.start_trade_session(user_id, 'sell', symbol_code)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{holding['name']} ({symbol_code})\n保有株数: {holding['quantity']}株\n現在価格: ¥{holding['current_price']:,}\n\n売却する株数を入力してください。")
    )


def handle_sell_short_start(event, symbol_code: str, user_id: str):
    """空売り開始"""
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="空売りは個別チャットでのみ可能です。")
        )
        return

    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    stock = stock_api.get_stock_by_code(symbol_code)
    if not stock:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="指定された銘柄が見つかりません。")
        )
        return

    # セッション開始
    stock_api.start_trade_session(user_id, 'short', symbol_code)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"【空売り】\n{stock['name']} ({symbol_code})\n現在価格: ¥{stock['current_price']:,}\n\n空売りする株数を入力してください。")
    )


def handle_buy_to_cover_start(event, symbol_code: str, user_id: str):
    """買い戻し開始"""
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="買い戻しは個別チャットでのみ可能です。")
        )
        return

    from core.api import show_loading_animation
    show_loading_animation(user_id, loading_seconds=5)

    shorts = stock_api.get_short_positions(user_id)
    # 合算
    total_short_qty = sum(s['quantity'] for s in shorts if s['symbol_code'] == symbol_code)

    if total_short_qty == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="この銘柄の空売りポジションを保有していません。")
        )
        return
    
    stock = stock_api.get_stock_by_code(symbol_code)

    # セッション開始
    stock_api.start_trade_session(user_id, 'cover', symbol_code)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"【買い戻し】\n{stock['name']} ({symbol_code})\n空売り残高: {total_short_qty}株\n現在価格: ¥{stock['current_price']:,}\n\n返済する株数を入力してください。")
    )


def handle_trade_quantity_input(event, user_id: str, message_text: str):
    """株数入力処理"""
    session = stock_api.get_session(user_id)

    if not session or session.get('step') != 'quantity':
        return False

    try:
        quantity = int(message_text)
        if quantity <= 0:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="1以上の数値を入力してください。")
            )
            return True

        # セッション更新
        session['quantity'] = quantity
        session['step'] = 'confirm'
        stock_api.update_session(user_id, session)

        # 確認FlexMessage表示
        stock = stock_api.get_stock_by_code(session['symbol_code'])
        if not stock:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="銘柄情報の取得に失敗しました。")
            )
            stock_api.end_session(user_id)
            return True

        confirmation_flex = stock_flex.get_trade_confirmation_flex(
            stock,
            session['trade_type'],
            quantity
        )
        line_bot_api.reply_message(event.reply_token, confirmation_flex)
        return True

    except ValueError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="数値を入力してください。")
        )
        return True


def handle_confirm_trade(event, trade_type: str, symbol_code: str, quantity: int, user_id: str):
    """取引確定処理"""
    # セッションが存在するか確認（重複実行防止）
    session = stock_api.get_session(user_id)
    if not session or session.get('step') != 'confirm':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ この取引は既に処理済み、またはキャンセルされています。")
        )
        return

    if trade_type == 'buy':
        success, message, result = stock_api.buy_stock(user_id, symbol_code, quantity)
    elif trade_type == 'sell':
        success, message, result = stock_api.sell_stock(user_id, symbol_code, quantity)
    elif trade_type == 'short':
        success, message, result = stock_api.sell_short(user_id, symbol_code, quantity)
    elif trade_type == 'cover':
        success, message, result = stock_api.buy_to_cover(user_id, symbol_code, quantity)
    else:
        success, message, result = False, "不明な取引タイプです", None

    # セッション終了
    stock_api.end_session(user_id)

    # 結果FlexMessage
    result_flex = stock_flex.get_trade_result_flex(
        success,
        trade_type,
        result,
        message if not success else ""
    )
    line_bot_api.reply_message(event.reply_token, result_flex)


def handle_cancel_trade(event, user_id: str):
    """取引キャンセル"""
    stock_api.end_session(user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="取引をキャンセルしました。")
    )


def handle_confirm_stock_account(event, account_id: int, user_id: str):
    """株式口座登録確定"""
    result = stock_api.create_stock_account(user_id, account_id)

    if result:
        if result.get('exists'):
            # 既に登録済みの場合はダッシュボードを表示
            dashboard = stock_flex.get_stock_dashboard(user_id, has_account=True)
            stock_api.end_session(user_id)
            line_bot_api.reply_message(event.reply_token, dashboard)
        else:
            # 新規登録完了後、自動的にダッシュボードを表示
            stock_api.end_session(user_id)
            dashboard = stock_flex.get_stock_dashboard(user_id, has_account=True)
            line_bot_api.reply_message(event.reply_token, dashboard)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 株式口座の登録に失敗しました。管理者にお問い合わせください。")
        )


def handle_stock_postback(event, data: dict, user_id: str):
    """株式関連のPostback処理"""
    action = data.get('action')

    if action == 'stock_list':
        handle_stock_list(event, user_id)

    elif action == 'my_holdings':
        handle_my_holdings(event, user_id)

    elif action == 'my_short_positions':
        handle_my_short_positions(event, user_id)

    elif action == 'market_news':
        handle_market_news(event)

    elif action == 'stock_detail':
        symbol = data.get('symbol')
        if symbol:
            handle_stock_detail(event, symbol, user_id)

    elif action == 'buy_stock':
        symbol = data.get('symbol')
        if symbol:
            handle_buy_stock_start(event, symbol, user_id)

    elif action == 'sell_stock':
        symbol = data.get('symbol')
        if symbol:
            handle_sell_stock_start(event, symbol, user_id)

    elif action == 'sell_short':
        symbol = data.get('symbol')
        if symbol:
            handle_sell_short_start(event, symbol, user_id)

    elif action == 'buy_to_cover':
        symbol = data.get('symbol')
        if symbol:
            handle_buy_to_cover_start(event, symbol, user_id)

    elif action == 'confirm_buy' or action == 'confirm_sell' or action == 'confirm_short' or action == 'confirm_cover':
        symbol = data.get('symbol')
        quantity = int(data.get('quantity', 0))
        trade_type = action.replace('confirm_', '')
        if symbol and quantity > 0:
            handle_confirm_trade(event, trade_type, symbol, quantity, user_id)

    elif action == 'cancel_trade':
        handle_cancel_trade(event, user_id)

    elif action == 'confirm_stock_account':
        account_id = int(data.get('account_id', 0))
        if account_id > 0:
            handle_confirm_stock_account(event, account_id, user_id)

    elif action == 'select_stock_account':
        account_id = int(data.get('account_id', 0))
        if account_id > 0:
            # 複数口座の場合の選択処理（簡易版）
            handle_confirm_stock_account(event, account_id, user_id)


def handle_stock_session(event, user_id: str, message_text: str):
    """株式セッション中の入力処理"""
    session = stock_api.get_session(user_id)

    if not session:
        return False

    session_type = session.get('type')

    if session_type == 'stock_trade':
        # 取引フロー
        return handle_trade_quantity_input(event, user_id, message_text)

    return False
