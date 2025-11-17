"""
1.グループチャット内で"?じゃんけん"と入力する。 ←達成
2.送信者に有効な銀行口座が存在し、最低参加費用（例:110JPY）を満たしているか確認。 ←達成
3.存在しない場合、口座開設を促すメッセージを送信。 ←達成
4.存在する場合、参加者の募集を開始し、参加希望者を募る。 ←達成
5.参加希望者は"?参加"と入力して参加表明を行う。 ←達成
6.送信者に有効な銀行口座が存在し、最低参加費用（例:110JPY）を満たしているか確認し、満たしていない場合は参加を拒否する。 ←達成
7.開始までなら"?キャンセル"で参加を取り消し可能とする。ホストがキャンセルした場合、全員の参加を取り消す。 ←達成
8.一定時間（例:1分）後、または"?開始"または参加人数5人で募集を締め切る。
9.参加者全員からベッド各110JPY(手数料約10%)を徴収(引き落とし)する。
10.参加者に対して、グループラインで「個別チャットでじゃんけんの手（グー、チョキ、パー）を選択して送信するよう」促す。
11.各参加者が手を選択し送信する。
12.20秒の猶予を与え、全員の手が揃うかタイムアウトを待つ。
13.タイムアウトしたユーザーはその時点で負けとする。
14.全員の手が揃ったら、じゃんけんの勝敗を判定する。
15.順位によってそれぞれの賞金を計算する。
16.3人以上の参加者がいる場合、同時に多人数じゃんけんを処理する。
17.順位に応じて賞金を分配する（例:1位200JPY、2位100JPY、3位40JPY）。
18.各順位の収支を含めた結果をグループチャットに表示する。
19.賞金を各参加者の銀行口座に送金する。
20.次のゲームの開催を促すメッセージを送信する。
注意点:
- 送金処理は銀行システムのAPIを使用して行う。
- 参加者が最低2人以上必要。
"""
from apps.minigame.minigames import Player, GameSession, Group, GroupManager, manager, check_account_existence_and_balance, create_game_session
from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# 口座が存在し、かつアクティブ状態であり、残金がmin_balanceを満たしているかどうかを確認。
"""
?じゃんけん
既に同じグループラインで進行中のじゃんけんゲームがある場合、そのゲームに参加を促す。
最初に?じゃんけんを送信したユーザーがホストとなり、そのユーザーがキャンセルまたは開始するまで募集を続ける。
"""

def play_rps_game(event, user_id, text, display_name, group_id, sessions):
    min_balance = 110  # 最低参加費用
    max_players = 5    # 募集上限（参加人数）
    # 既に同グループで進行中（募集中）のじゃんけんがあるかチェック
    try:
        existing_session = manager.get_session(group_id)
    except Exception:
        existing_session = None

    from apps.minigame.minigames import GameState
    if existing_session and getattr(existing_session, "game_type", None) == "rps_game" and getattr(existing_session, "state", None) == GameState.RECRUITING:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"このグループでは既に{existing_session.host_user_id}がじゃんけんの参加者を募集しています。参加する場合は'?参加'と入力してください（募集は最大{getattr(existing_session,'max_players','不明')}名まで）。")
        )
        return

    if not check_account_existence_and_balance(None, user_id, min_balance):
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=f"{display_name} 様、申し訳ございませんが、じゃんけんゲームを開始するためには有効な銀行口座と最低残高 {min_balance} JPY が必要です。"),
            TextSendMessage(text="口座をお持ちでない場合は、塩爺との個別チャットにて'?口座開設' と入力して口座を開設してください。")]
        )
        return

    # セッション作成
    create_game_session(
        group_id=group_id,
        game_type="rps_game",
        host_user_id=user_id,
        min_balance=min_balance,
        max_players=max_players,
        host_display_name=display_name
    )

    # manager に登録されたセッションが取得できれば max_players を明示的に設定
    try:
        session = manager.get_session(group_id)
        if session:
            setattr(session, "max_players", max_players)
    except Exception:
        # manager.get_session が使えない場合は無視（minigame 側で対応が必要）
        session = None

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{display_name}が参加者を募集しています。参加希望の方は'?参加'と入力してください。募集は最大{max_players}名で締め切ります。")
    )

