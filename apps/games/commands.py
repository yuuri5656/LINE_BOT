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
import psycopg2
import config


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
