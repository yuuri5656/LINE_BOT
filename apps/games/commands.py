"""
ゲーム機能関連のコマンドハンドラー
"""
from linebot.models import TextSendMessage
from core.api import line_bot_api
from apps.games.rps_game import play_rps_game
from apps.games.minigames import (
    manager, GameState, join_game_session, cancel_game_session,
    reset_game_session, submit_player_move
)
from apps.games.session_manager import individual_game_manager
from apps.games import game_flex, blackjack_flex, blackjack_game
from apps.banking.chip_service import get_chip_balance, batch_lock_chips, distribute_chips
import psycopg2
import config
import urllib.parse
from datetime import datetime
from typing import Dict


def handle_janken_start(event, user_id, text, display_name, group_id, sessions):
    """じゃんけんゲーム開始コマンド"""
    if event.source.type != 'group':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="じゃんけんはグループチャットでのみ利用可能です。"))
        return

    grp = manager.groups.get(group_id, None)
    if grp is None or grp.current_game is None:
        play_rps_game(event, user_id, text, display_name, group_id, sessions)
        return

    state = getattr(grp.current_game, "state", None)
    if state == GameState.RECRUITING:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{display_name} 様、現在このグループではゲームを募集中です。\n是非'?参加'と入力して参加してみてください。")
        )
        return
    if state == GameState.IN_PROGRESS:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{display_name} 様、現在このグループではゲームが進行中です。\nしばらくお待ちの上、再度お試しください。")
        )
        return


def handle_join_game(event, user_id, display_name, group_id):
    """ゲーム参加コマンド"""
    if event.source.type != 'group':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ゲーム参加はグループチャットでのみ利用可能です。"))
        return

    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        join_message = join_game_session(group_id, user_id, display_name, conn)
    finally:
        conn.close()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=join_message))


def handle_game_cancel(event, user_id, group_id):
    """ゲームキャンセルコマンド"""
    if event.source.type != 'group':
        return False

    group = manager.groups.get(group_id)
    if not group or not group.current_game:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="セッションをキャンセル出来ませんでした。"))
        return True

    host_can_cancel = getattr(group.current_game, "state", None) != GameState.IN_PROGRESS

    if group.current_game.host_user_id == user_id and host_can_cancel:
        reset_game_session(group_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ホストがキャンセルしたため、全員の参加を取り消しました。")
        )
        return True

    participant_can_cancel = getattr(group.current_game, "state", None) == GameState.RECRUITING
    if participant_can_cancel:
        if user_id in group.current_game.players:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=cancel_game_session(group_id, user_id))
            )
            return True

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="セッションをキャンセル出来ませんでした。")
    )
    return True


def handle_game_start(event, user_id, group_id):
    """ゲーム開始コマンド"""
    if event.source.type != 'group':
        return

    group = manager.groups.get(group_id)
    if group and group.current_game and group.current_game.state == GameState.RECRUITING and group.current_game.host_user_id == user_id:
        print(f"Players listed for game start: {group.current_game.players}")
        try:
            from apps.games.minigames import start_game_session
            msg = start_game_session(group_id, line_bot_api, timeout_seconds=30, reply_token=event.reply_token)
            if msg and isinstance(msg, str):
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        except Exception as e:
            print(f"Exception in start_game_session: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"ゲームの開始に失敗しました。\nエラー: {str(e)}"))
        return
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ゲームを開始できませんでした。ホストのみが開始できます。")
        )


def handle_player_move(event, user_id, text):
    """プレイヤーの手の入力処理"""
    if event.source.type == 'user':
        if text.strip() in ["グー", "ぐー", "チョキ", "ちょき", "パー", "ぱー"]:
            submit_player_move(user_id, text.strip(), line_bot_api, reply_token=event.reply_token)
            return True
    return False


# ===== 個別チャット用ゲーム機能 =====

def handle_game_menu(event, user_id):
    """
    ゲームメニュー表示（個別チャット専用）

    Args:
        event: LINEイベント
        user_id: ユーザーID
    """
    # 個別チャット限定
    if event.source.type != 'user':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ゲーム機能は個別チャット専用です。\nBOTに直接メッセージを送信してください。")
        )
        return

    # チップ残高確認
    try:
        balance_info = get_chip_balance(user_id)
        chip_balance = balance_info.get('available', 0)

        # 最小ベット額をチェック（10チップ）
        if chip_balance < 10:
            flex_message = game_flex.get_insufficient_chips_message(chip_balance, 10)
            line_bot_api.reply_message(event.reply_token, flex_message)
            return

        # ゲーム選択カルーセルを表示
        carousel = game_flex.get_game_selection_carousel()
        line_bot_api.reply_message(event.reply_token, carousel)

    except Exception as e:
        print(f"Error in handle_game_menu: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ゲームメニューの表示中にエラーが発生しました。")
        )


def handle_game_selection(event, user_id, data: Dict):
    """
    ゲーム選択処理（postback）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        data: postbackデータ {'game_type': str, 'min_bet': str}
    """
    game_type = data.get('game_type', 'blackjack')
    min_bet = int(data.get('min_bet', 10))

    try:
        # チップ残高確認
        balance_info = get_chip_balance(user_id)
        chip_balance = balance_info.get('available', 0)

        if chip_balance < min_bet:
            flex_message = game_flex.get_insufficient_chips_message(chip_balance, min_bet)
            line_bot_api.reply_message(event.reply_token, flex_message)
            return

        # セッション作成（ベット選択フェーズ）
        individual_game_manager.create_session(user_id, game_type, {
            'type': 'betting',
            'current_bet': 0,
            'chip_balance': chip_balance,
            'created_at': datetime.now()
        })

        # ベット選択画面を表示
        flex_message = blackjack_flex.get_betting_screen(0, chip_balance, game_type)
        line_bot_api.reply_message(event.reply_token, flex_message)

    except Exception as e:
        print(f"Error in handle_game_selection: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ゲーム開始中にエラーが発生しました。")
        )


def handle_add_bet(event, user_id, data: Dict):
    """
    ベット額追加処理（postback）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        data: postbackデータ {'amount': str, 'game_type': str}
    """
    session = individual_game_manager.get_session(user_id)
    if not session or session.get('type') != 'betting':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ベット選択画面が見つかりません。\n「?ゲーム」から再度開始してください。")
        )
        return

    try:
        amount = int(data.get('amount', 0))
        game_type = data.get('game_type', 'blackjack')

        # 現在のベット額に加算
        current_bet = session.get('current_bet', 0)
        new_bet = current_bet + amount

        # チップ残高確認
        balance_info = get_chip_balance(user_id)
        chip_balance = balance_info.get('available', 0)

        # 最大ベット制限（2000チップまたは残高）
        max_bet = min(2000, chip_balance)

        if new_bet > max_bet:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ベット額が上限を超えています。\n最大ベット額: {max_bet}チップ")
            )
            return

        # セッション更新
        individual_game_manager.update_session(user_id, {
            'current_bet': new_bet,
            'chip_balance': chip_balance
        })

        # ベット画面を更新
        flex_message = blackjack_flex.get_betting_screen(new_bet, chip_balance, game_type)
        line_bot_api.reply_message(event.reply_token, flex_message)

    except Exception as e:
        print(f"Error in handle_add_bet: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ベット追加中にエラーが発生しました。")
        )


def handle_reset_bet(event, user_id, data: Dict):
    """
    ベット額リセット処理（postback）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        data: postbackデータ {'game_type': str}
    """
    session = individual_game_manager.get_session(user_id)
    if not session:
        return

    try:
        game_type = data.get('game_type', 'blackjack')

        # チップ残高確認
        balance_info = get_chip_balance(user_id)
        chip_balance = balance_info.get('available', 0)

        # ベット額を0にリセット
        individual_game_manager.update_session(user_id, {
            'current_bet': 0,
            'chip_balance': chip_balance
        })

        # ベット画面を更新
        flex_message = blackjack_flex.get_betting_screen(0, chip_balance, game_type)
        line_bot_api.reply_message(event.reply_token, flex_message)

    except Exception as e:
        print(f"Error in handle_reset_bet: {e}")


def handle_confirm_bet(event, user_id, data: Dict):
    """
    ベット確定・ゲーム開始処理（postback）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        data: postbackデータ {'game_type': str}
    """
    session = individual_game_manager.get_session(user_id)
    if not session or session.get('type') != 'betting':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ベット選択画面が見つかりません。")
        )
        return

    try:
        bet_amount = session.get('current_bet', 0)

        # 最小ベットチェック
        if bet_amount < 10:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="最小ベット額は10チップです。")
            )
            return

        # チップ残高確認
        balance_info = get_chip_balance(user_id)
        chip_balance = balance_info.get('available', 0)

        if chip_balance < bet_amount:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="チップ残高が不足しています。")
            )
            return

        # チップをロック
        game_session_id = f"blackjack_{user_id}_{datetime.now().timestamp()}"
        lock_result = batch_lock_chips([{
            'user_id': user_id,
            'amount': bet_amount,
            'game_session_id': game_session_id
        }])

        if not lock_result.get('success'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="チップのロックに失敗しました。")
            )
            return

        # ブラックジャックゲーム開始
        deck = blackjack_game.create_deck()
        player_hand, dealer_hand, deck = blackjack_game.deal_initial_cards(deck)

        player_total = blackjack_game.calculate_hand_value(player_hand)
        dealer_showing = dealer_hand[0]['value']

        # 即座のブラックジャック判定
        player_bj = blackjack_game.is_blackjack(player_hand)
        dealer_bj = blackjack_game.is_blackjack(dealer_hand)

        # セッション更新（プレイ中）
        individual_game_manager.update_session(user_id, {
            'type': 'playing',
            'bet_amount': bet_amount,
            'locked_chips': bet_amount,
            'game_session_id': game_session_id,
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'is_doubled': False
        })

        # プレイヤーがブラックジャックの場合、即座に結果表示
        if player_bj:
            # ディーラーもブラックジャックかチェック
            result = blackjack_game.calculate_winner(player_hand, dealer_hand, bet_amount, False)

            # チップ配分
            distribute_chips({
                user_id: {
                    'locked': bet_amount,
                    'payout': result['payout']  # 純利益
                }
            }, game_session_id)

            # 新しい残高
            new_balance_info = get_chip_balance(user_id)
            new_chip_balance = new_balance_info.get('balance', 0)

            # 結果画面表示
            flex_message = blackjack_flex.get_result_screen(
                player_hand, dealer_hand,
                result['player_total'], result['dealer_total'],
                result['result'], bet_amount, result['payout'],
                new_chip_balance
            )

            # セッション削除
            individual_game_manager.clear_session(user_id)

            line_bot_api.reply_message(event.reply_token, flex_message)
            return

        # 通常のゲーム画面表示
        can_double = blackjack_game.can_double_down(player_hand, chip_balance - bet_amount, bet_amount)

        flex_message = blackjack_flex.get_game_screen(
            player_hand, dealer_hand,
            player_total, dealer_showing,
            bet_amount, can_double, True
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    except Exception as e:
        print(f"Error in handle_confirm_bet: {e}")
        import traceback
        traceback.print_exc()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"ゲーム開始中にエラーが発生しました。\n{str(e)}")
        )


def handle_blackjack_action(event, user_id, action: str):
    """
    ブラックジャックアクション処理（hit/stand/double）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        action: アクション ('hit', 'stand', 'double')
    """
    session = individual_game_manager.get_session(user_id)
    if not session or session.get('type') != 'playing':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ゲームセッションが見つかりません。")
        )
        return

    try:
        player_hand = session['player_hand']
        dealer_hand = session['dealer_hand']
        deck = session['deck']
        bet_amount = session['bet_amount']
        game_session_id = session['game_session_id']
        is_doubled = session.get('is_doubled', False)

        # HIT処理
        if action == 'hit':
            player_hand, deck = blackjack_game.hit_card(player_hand, deck)
            player_total = blackjack_game.calculate_hand_value(player_hand)

            # セッション更新
            individual_game_manager.update_session(user_id, {
                'player_hand': player_hand,
                'deck': deck
            })

            # バースト判定
            if blackjack_game.is_bust(player_hand):
                _finish_blackjack_game(event, user_id, session)
                return

            # ゲーム画面更新
            dealer_showing = dealer_hand[0]['value']
            balance_info = get_chip_balance(user_id)
            available_balance = balance_info.get('available', 0)
            can_double = blackjack_game.can_double_down(player_hand, available_balance, bet_amount)

            flex_message = blackjack_flex.get_game_screen(
                player_hand, dealer_hand,
                player_total, dealer_showing,
                bet_amount, can_double, True
            )
            line_bot_api.reply_message(event.reply_token, flex_message)

        # STAND処理
        elif action == 'stand':
            _finish_blackjack_game(event, user_id, session)

        # DOUBLE DOWN処理
        elif action == 'double':
            # チップ残高確認
            balance_info = get_chip_balance(user_id)
            available_balance = balance_info.get('available', 0)

            if not blackjack_game.can_double_down(player_hand, available_balance, bet_amount):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="ダブルダウンできません。")
                )
                return

            # 追加のチップをロック
            additional_lock_result = batch_lock_chips([{
                'user_id': user_id,
                'amount': bet_amount,
                'game_session_id': game_session_id + '_double'
            }])

            if not additional_lock_result.get('success'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="チップのロックに失敗しました。")
                )
                return

            # ベット額を2倍に
            new_bet_amount = bet_amount * 2

            # 1枚だけ引く
            player_hand, deck = blackjack_game.process_double_down(player_hand, deck)

            # セッション更新
            individual_game_manager.update_session(user_id, {
                'player_hand': player_hand,
                'deck': deck,
                'bet_amount': new_bet_amount,
                'locked_chips': new_bet_amount,
                'is_doubled': True
            })

            # 自動的にゲーム終了
            _finish_blackjack_game(event, user_id, session, is_doubled=True)

    except Exception as e:
        print(f"Error in handle_blackjack_action: {e}")
        import traceback
        traceback.print_exc()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"アクション処理中にエラーが発生しました。\n{str(e)}")
        )


def _finish_blackjack_game(event, user_id: str, session: Dict, is_doubled: bool = False):
    """
    ブラックジャックゲーム終了処理（内部関数）

    Args:
        event: LINEイベント
        user_id: ユーザーID
        session: セッションデータ
        is_doubled: ダブルダウンしたか
    """
    try:
        player_hand = session['player_hand']
        dealer_hand = session['dealer_hand']
        deck = session['deck']
        bet_amount = session['bet_amount']
        game_session_id = session['game_session_id']

        # ディーラーのプレイ（プレイヤーがバーストしていない場合）
        if not blackjack_game.is_bust(player_hand):
            dealer_hand, deck = blackjack_game.dealer_play(dealer_hand, deck)

        # 勝敗判定
        result = blackjack_game.calculate_winner(
            player_hand, dealer_hand, bet_amount,
            is_doubled or session.get('is_doubled', False)
        )

        # チップ配分
        # payoutは総額(ベット額+利益)を含むため、そのまま配分
        payout = result['payout']
        distribute_chips({
            user_id: {
                'locked': bet_amount,
                'payout': payout
            }
        }, game_session_id)

        # 新しい残高
        new_balance_info = get_chip_balance(user_id)
        new_chip_balance = new_balance_info.get('balance', 0)

        # 結果画面表示
        flex_message = blackjack_flex.get_result_screen(
            player_hand, dealer_hand,
            result['player_total'], result['dealer_total'],
            result['result'], bet_amount, payout,
            new_chip_balance
        )

        # セッション削除
        individual_game_manager.clear_session(user_id)

        line_bot_api.reply_message(event.reply_token, flex_message)

    except Exception as e:
        print(f"Error in _finish_blackjack_game: {e}")
        import traceback
        traceback.print_exc()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"ゲーム終了処理中にエラーが発生しました。\n{str(e)}")
        )
