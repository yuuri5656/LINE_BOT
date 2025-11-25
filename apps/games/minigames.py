# 経済機能
# ミニゲームによってポイントを獲得・消費できる機能
# ユーザー同士でのポイントの送受信も可能
# ユーザー同士で対戦可能
# ポイントランキング機能
# ポイント履歴閲覧機能
# ポイントによってガチャを回すことができ、アイテムを獲得可能
# 1.通貨を実装する。 ←銀行機能として実装
# 1-1.通貨を管理するデータベーステーブルを作成する。 ←銀行機能の実装によって達成
# 1-2.通貨の獲得・消費の関数を実装する。

from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime
from enum import Enum
from linebot.models import TextSendMessage, FlexSendMessage
from apps.banking.api import banking_api


def create_game_start_flex_message(player_names, timeout_seconds):
    """ゲーム開始時のFlexMessage作成（参加者リスト表示）"""
    # 参加者リストのコンテンツを作成
    player_contents = []
    for i, name in enumerate(player_names, 1):
        player_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{i}.",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": name,
                    "size": "sm",
                    "color": "#111111",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "margin": "md"
        })
    
    return FlexSendMessage(
        alt_text="じゃんけんゲーム開始",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎮",
                        "size": "xxl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": "ゲーム開始!",
                        "size": "xl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#4CAF50",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "参加者",
                        "size": "lg",
                        "weight": "bold",
                        "color": "#111111",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": player_contents,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "⏰ 手を選んでください",
                                "size": "md",
                                "weight": "bold",
                                "color": "#FF6B6B",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "個別チャットで「グー」「チョキ」「パー」のいずれかを送信してください。",
                                "size": "xs",
                                "color": "#999999",
                                "wrap": True,
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"制限時間: {timeout_seconds}秒",
                                "size": "sm",
                                "color": "#FF6B6B",
                                "align": "center",
                                "weight": "bold",
                                "margin": "md"
                            }
                        ],
                        "margin": "xl"
                    }
                ],
                "spacing": "sm",
                "paddingAll": "20px"
            }
        }
    )


class GameState(Enum):
    RECRUITING = "recruiting"
    RECRUITMENT_CLOSED = "recruitment_closed"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

# ミニゲームのセッション管理用データ構造
@dataclass
class Player:
    user_id: str
    display_name: str
    data: str = ""  # じゃんけんの手など

@dataclass
class GameSession:
    game_type: str       # 例: "rps_game"
    # 明確な状態管理のため Enum を利用
    state: GameState = GameState.RECRUITING
    created_at: datetime = field(default_factory=datetime.now)
    min_balance: int = 0  # 参加に必要な最低残高
    host_user_id: str = ""  # ゲーム開始者
    max_players: int = 0    # 募集上限
    players: Dict[str, Player] = field(default_factory=dict)
    # 実行中のゲーム用フィールド
    start_time: datetime = None
    deadline: datetime = None
    timer: object = None

@dataclass
class Group:
    group_id: str
    current_game: GameSession = None  # このグループで開催中のゲーム

@dataclass
class GroupManager:
    groups: Dict[str, Group] = field(default_factory=dict) # グループIDをキーにGroupオブジェクトを管理

    # 追加: グループに紐づくセッション取得ヘルパー
    def get_session(self, group_id: str):
        grp = self.groups.get(group_id)
        if not grp:
            return None
        return grp.current_game

manager = GroupManager()

# 口座が存在し、かつアクティブ状態であり、残金がmin_balanceを満たしているかどうかを確認。
def check_account_existence_and_balance(conn, user_id, min_balance):
    """
    ミニゲーム用に登録された口座の存在と残高を確認する。
    ミニゲーム口座が未登録の場合はFalseを返す。
    """
    try:
        # ミニゲーム口座が登録されているか確認
        minigame_acc_info = banking_api.get_minigame_account_info(user_id)
        if not minigame_acc_info:
            return False  # ミニゲーム口座が未登録
        
        # 残高チェック
        try:
            balance_str = minigame_acc_info.get('balance')
            if balance_str is None:
                return False
            from decimal import Decimal
            balance = Decimal(balance_str)
            return balance >= min_balance
        except Exception:
            return False
    except Exception:
        return False


def fixed_prize_distribution(bets, fee_rate=0.1):
    """
    小規模（2～5人）向けの固定分配方式。
    1位圧倒的、下位にも少額分配。
    """
    N = len(bets)
    if N < 2 or N > 5:
        raise ValueError("この関数は2〜5人向けです。")

    total_bet = sum(bets)
    fee = int(round(total_bet * fee_rate))
    prize_pool = total_bet - fee

    if N == 2:
        ratios = [0.85, 0.15]
    elif N == 3:
        ratios = [0.75, 0.15, 0.10]
    elif N == 4:
        ratios = [0.65, 0.20, 0.10, 0.05]
    elif N == 5:
        ratios = [0.60, 0.20, 0.10, 0.05, 0.05]

    prizes_float = [prize_pool * r for r in ratios]
    prizes_int = [int(p) for p in prizes_float]
    remainder = prize_pool - sum(prizes_int)
    prizes_int[0] += remainder

    return prizes_int, fee

# セッション作成処理
def create_game_session(group_id: str, game_type: str, host_user_id: str, min_balance: int, max_players: int = 0, host_display_name: str = None):
    # ホストはセッション作成時点で参加者として追加する
    players = {}
    if host_user_id:
        players[host_user_id] = Player(user_id=host_user_id, display_name=host_display_name or host_user_id)

    manager.groups[group_id] = Group(
        group_id=group_id,
        current_game=GameSession(
            game_type=game_type,
            state=GameState.RECRUITING,
            min_balance=min_balance,
            host_user_id=host_user_id,
            max_players=max_players,
            players=players
        )
    )

# 参加処理
def join_game_session(group_id: str, user_id: str, display_name: str, conn):
    group = manager.groups.get(group_id)
    if not group:
        return "このグループではゲームが開催されていません。"

    # --- 追加: 別グループで既に参加中のユーザーは参加不可 ---
    def find_user_participation(uid: str):
        """
        uid が別のグループで既に参加（募集中または進行中）しているかを探す。
        見つかった場合は (group_id, session) を返す。見つからなければ (None, None)。
        """
        for gid, grp in manager.groups.items():
            if not grp or not grp.current_game:
                continue
            sess = grp.current_game
            if sess.state in (GameState.RECRUITING, GameState.IN_PROGRESS) and uid in sess.players:
                return gid, sess
        return None, None

    found_gid, found_sess = find_user_participation(user_id)
    if found_gid and found_gid != group_id:
        return "あなたは既に他のグループでゲームに参加しています。先にそちらの参加をキャンセルしてください。"

    # グループに現在進行中のゲームがあるか確認
    if not group.current_game:
        return "このグループではゲームが開催されていません。"

    # ゲームの状態がプレイヤー待ち（募集中）か確認
    if group.current_game.state != GameState.RECRUITING:
        return "ゲームは現在プレイヤー待ち（募集中）ではありません。\nしばらくお待ちの上、再度お試しください。"

    # 募集上限をチェック（既に締め切られている/満員）
    if group.current_game.max_players and len(group.current_game.players) >= group.current_game.max_players:
        # 既に満員なので締め切り状態に更新
        group.current_game.state = GameState.RECRUITMENT_CLOSED
        return f"募集は既に締め切られています（最大 {group.current_game.max_players} 名）。"

    # プレイヤーがすでに参加していないか確認
    if user_id in group.current_game.players:
        return "あなたはは既にゲームに参加しています。"

    # 口座存在と最低残高の確認
    if not check_account_existence_and_balance(conn, user_id, group.current_game.min_balance):
        return f"ミニゲーム用口座が登録されていないか、最低残高({group.current_game.min_balance} JPY)を満たしていません。\n\n塩爺との個別チャット(1対1トーク)にて '?ミニゲーム口座登録' と入力して、お持ちの口座をミニゲーム用として登録してください。"

    # すべての条件を満たしていれば参加
    group.current_game.players[user_id] = Player(user_id=user_id, display_name=display_name)

    # 参加後に上限到達を判定して自動で募集を締め切る
    if group.current_game.max_players and len(group.current_game.players) >= group.current_game.max_players:
        group.current_game.state = GameState.RECRUITMENT_CLOSED
        return f"{display_name}の参加を受け付けました。募集は最大人数に達したため締め切りました。"

    return f"{display_name}の参加を受け付けました。ゲーム開始までお待ちください。"

# 参加キャンセル処理
def cancel_game_session(group_id: str, user_id: str):
    group = manager.groups.get(group_id)
    if not group or not group.current_game:
        return "このグループではゲームが開催されていません。"


    # ゲームが既に開始されている場合はキャンセル不可
    if group.current_game.state == GameState.IN_PROGRESS:
        return "ゲームは既に開始されています。キャンセルできません。"

    # ホストがキャンセルした場合は全員取り消し（ゲーム開始前なら可能）
    if user_id == group.current_game.host_user_id:
        group.current_game = None
        return "ホストが募集をキャンセルしました。参加者全員の参加が取り消されました。"

    # プレイヤーが参加しているか確認
    if user_id not in group.current_game.players:
        return "あなたは現在ゲームに参加していません。"

    # 参加受付中であれば参加をキャンセル可能
    if group.current_game.state != GameState.RECRUITING:
        return "現在は参加受付を行っていないため、参加キャンセルできません。"

    # 参加をキャンセル
    del group.current_game.players[user_id]
    return "あなたの参加をキャンセルしました。"

# セッションリセット処理
def reset_game_session(group_id: str):
    group = manager.groups.get(group_id)
    if group:
        group.current_game = None


# --- 以下、ゲーム進行用ユーティリティ ---
def start_game_session(group_id: str, line_bot_api, timeout_seconds: int = 30, reply_token=None):
    from threading import Timer
    from datetime import timedelta
    group = manager.groups.get(group_id)
    if not group or not group.current_game:
        return "このグループではゲームが開催されていません。"

    session = group.current_game
    if session.state != GameState.RECRUITING:
        return "ゲームは現在開始できる状態ではありません。"

    session.state = GameState.IN_PROGRESS
    session.start_time = datetime.now()
    session.deadline = session.start_time + timedelta(seconds=timeout_seconds)

    # 参加費を徴収(銀行APIを利用 - 口座番号ベース)
    paid = []
    failed = []
    for uid in list(session.players.keys()):
        try:
            # ミニゲーム口座情報を取得
            minigame_acc_info = banking_api.get_minigame_account_info(uid)
            if not minigame_acc_info:
                raise ValueError("Minigame account not registered")
            account_number = minigame_acc_info.get('account_number')
            branch_code = minigame_acc_info.get('branch_code')
            if not account_number or not branch_code:
                raise ValueError("Account number or branch code not found")
            # 口座番号ベースで引き落とし
            result = banking_api.withdraw_by_account(account_number, branch_code, session.min_balance)
            paid.append(uid)
            print(f"start_game_session: withdraw success for user={uid} amount={session.min_balance}")
        except Exception as e:
            print(f"start_game_session: withdraw failed for user={uid} amount={session.min_balance} error={e}")
            failed.append(uid)
    # 支払い失敗したユーザーは参加者リストから除外
    for uid in failed:
        if uid in session.players:
            del session.players[uid]
    if not paid:
        return "参加費の徴収に全員失敗しました。"

    # デバッグ出力: 支払い状況と残存プレイヤー
    try:
        print(f"start_game_session: group={group_id} paid={paid} failed={failed} remaining_players={list(session.players.keys())}")
    except Exception:
        pass

    # テスト用: 1人でもゲーム開始できるよう条件変更（元に戻す場合は <2 → <2 に戻す）
    try:
        remaining = list(session.players.keys())
        if len(remaining) < 1:  # ←元は <2
            # 返金処理(支払い済みのユーザーに戻す - 口座番号ベース)
            for uid in paid:
                try:
                    minigame_acc_info = banking_api.get_minigame_account_info(uid)
                    if minigame_acc_info:
                        account_number = minigame_acc_info.get('account_number')
                        branch_code = minigame_acc_info.get('branch_code')
                        if account_number and branch_code:
                            banking_api.deposit_by_account(account_number, branch_code, session.min_balance)
                except Exception:
                    try:
                        print(f"start_game_session: refund failed for user={uid} amount={session.min_balance}")
                    except Exception:
                        pass

            # セッションを中止してグループに通知（1通にまとめる）
            try:
                msg = "参加者がいないため、ゲームを開始できません。\nゲームの開始に失敗しました。"
                if reply_token:
                    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
                else:
                    line_bot_api.push_message(group_id, TextSendMessage(text=msg))
            except Exception as e:
                # 失敗時はエラー内容も通知
                err_msg = f"ゲーム開始エラー: {str(e)}"
                try:
                    if reply_token:
                        line_bot_api.reply_message(reply_token, TextSendMessage(text=err_msg))
                    else:
                        line_bot_api.push_message(group_id, TextSendMessage(text=err_msg))
                except Exception:
                    pass
            # セッションをクリア
            group.current_game = None
            return "参加者がいないため、ゲームを開始できませんでした。"
    except Exception as e:
        # 失敗時はエラー内容も通知
        try:
            if reply_token:
                line_bot_api.reply_message(reply_token, TextSendMessage(text=f"ゲーム開始処理中にエラーが発生しました: {str(e)}"))
            else:
                line_bot_api.push_message(group_id, TextSendMessage(text=f"ゲーム開始処理中にエラーが発生しました: {str(e)}"))
        except Exception:
            pass
        # セッションをクリア
        group.current_game = None
        return f"ゲーム開始処理中にエラーが発生しました: {str(e)}"

    # 支払いできなかったユーザーを通知
    if failed:
        try:
            failed_names = [p.display_name for uid, p in list(session.players.items()) if uid in failed]
        except Exception:
            failed_names = []
    player_names = [p.display_name for p in session.players.values()]
    try:
        flex_msg = create_game_start_flex_message(player_names, timeout_seconds)
        if reply_token:
            line_bot_api.reply_message(reply_token, flex_msg)
        else:
            line_bot_api.push_message(group_id, flex_msg)
    except Exception:
        pass

    # 個別チャットへの案内メッセージ送信を削除

    # タイムアウトで自動終了するタイマーを設定
    def _finish():
        try:
            finish_game_session(group_id, line_bot_api)
        except Exception:
            pass

    timer = Timer(timeout_seconds, _finish)
    session.timer = timer
    timer.daemon = True
    timer.start()

    return None  # 成功時はNoneを返す


def find_session_by_user(user_id: str):
    # 参加中で進行中のセッションを検索
    # デバッグ用ログを追加して現状を確認しやすくする
    try:
        for gid, grp in manager.groups.items():
            if not grp or not grp.current_game:
                #print(f"find_session_by_user: group {gid} has no current_game")
                continue
            sess = grp.current_game
            # サマリ出力（デバッグ）
            try:
                player_keys = list(sess.players.keys()) if sess.players else []
            except Exception:
                player_keys = []
            print(f"find_session_by_user: checking group={gid} state={sess.state} players={player_keys}")
            if sess.state == GameState.IN_PROGRESS and user_id in sess.players:
                print(f"find_session_by_user: match found in group={gid} for user={user_id}")
                return gid, sess
    except Exception as e:
        print(f"find_session_by_user: error while searching sessions: {e}")
    return None, None


def submit_player_move(user_id: str, move: str, line_bot_api, reply_token=None):
    # move は "グー","チョキ","パー" のいずれかを受け付ける
    normalized = None
    key = move.strip()
    if key in ["グー","ぐー","ｸﾞｰ"]:
        normalized = "グー"
    elif key in ["チョキ","ちょき"]:
        normalized = "チョキ"
    elif key in ["パー","ぱー"]:
        normalized = "パー"
    else:
        if reply_token:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="無効な手です。個別チャットで「グー」「チョキ」「パー」のいずれかを送信してください。"))
        return "invalid"

    gid, session = find_session_by_user(user_id)
    if not session:
        if reply_token:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="現在参加中の進行中ゲームが見つかりません。グループ内で募集が行われているか確認してください。"))
        return "no_session"

    player = session.players.get(user_id)
    if not player:
        if reply_token:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="あなたは現在このゲームに参加していません。"))
        return "not_participant"

    if player.data:
        if reply_token:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="既に手が記録されています。変更はできません。"))
        return "already_submitted"

    player.data = normalized
    if reply_token:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"{player.display_name} さんの手「{normalized}」を受け付けました。"))

    # 全員の手が揃ったら終了処理
    all_in = all(p.data for p in session.players.values()) and len(session.players) >= 2
    if all_in:
        try:
            if session.timer:
                session.timer.cancel()
        except Exception:
            pass
        finish_game_session(gid, line_bot_api)

    return "ok"


def finish_game_session(group_id: str, line_bot_api):
    group = manager.groups.get(group_id)
    if not group or not group.current_game:
        return

    session = group.current_game
    # デバッグ出力: 終了時のセッション情報
    try:
        print(f"finish_game_session: group={group_id} state={session.state} players={list(session.players.keys())}")
    except Exception:
        pass
    session.state = GameState.FINISHED

    players = list(session.players.values())

    def beats(a, b):
        if a == b:
            return 0
        rules = {"グー":"チョキ", "チョキ":"パー", "パー":"グー"}
        return 1 if rules.get(a) == b else -1

    scores = {p.user_id: 0 for p in players}
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            pi = players[i]
            pj = players[j]
            if not pi.data and not pj.data:
                continue
            if not pi.data:
                scores[pj.user_id] += 1
                scores[pi.user_id] -= 1
                continue
            if not pj.data:
                scores[pi.user_id] += 1
                scores[pj.user_id] -= 1
                continue
            res = beats(pi.data, pj.data)
            if res == 1:
                scores[pi.user_id] += 1
                scores[pj.user_id] -= 1
            elif res == -1:
                scores[pj.user_id] += 1
                scores[pi.user_id] -= 1

    ranked = sorted(players, key=lambda p: scores.get(p.user_id, 0), reverse=True)

    n = len(players)
    # 賞金計算は固定分配方式を使用
    fee = 0  # 初期化
    try:
        bets = [session.min_balance for _ in ranked]
        prizes, fee = fixed_prize_distribution(bets, fee_rate=0.1)
        payouts = {ranked[i].user_id: prizes[i] for i in range(len(ranked))}
    except Exception:
        # フォールバック: 以前の簡易分配（等比）
        n = len(players)
        pot = n * session.min_balance
        distributable = int(pot * 0.9)
        weight_map = {}
        total_weight = 0
        for p in players:
            w = max(scores.get(p.user_id, 0), 0) + 1
            weight_map[p.user_id] = w
            total_weight += w
        payouts = {}
        for p in players:
            share = int(distributable * weight_map[p.user_id] / total_weight) if total_weight > 0 else 0
            payouts[p.user_id] = share
        fee = pot - distributable  # フォールバック時も手数料を計算

    # モダンなFlexMessageで結果を表示する
    # 各プレイヤーの収支は『受け取った賞金 - 参加費 - (手数料の均等分配)』で計算する
    flex_players = []
    fee_share_per_player = (fee // n) if n > 0 else 0
    for idx, p in enumerate(ranked, start=1):
        hand = p.data if p.data else "(未提出)"
        sc = scores.get(p.user_id, 0)
        pay = payouts.get(p.user_id, 0)
        profit = pay - session.min_balance - fee_share_per_player
        # 表示用の符号と色
        sign = f"+{profit}" if profit >= 0 else f"{profit}"
        color = "#0b8043" if profit > 0 else ("#000000" if profit == 0 else "#d32f2f")

        player_row = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"{idx}位", "size": "sm", "weight": "bold", "color": "#666666", "flex": 1},
                {"type": "text", "text": p.display_name, "size": "sm", "weight": "bold", "flex": 4},
                {"type": "text", "text": hand, "size": "sm", "align": "end", "flex": 2, "color": "#666666"},
                {"type": "text", "text": f"{sign} JPY", "size": "sm", "align": "end", "flex": 3, "weight": "bold", "color": color}
            ]
        }
        flex_players.append(player_row)

    # 賞金の支払い(口座番号ベース)
    try:
        for uid, amount in payouts.items():
            if amount <= 0:
                continue
            try:
                # ミニゲーム口座情報を取得
                minigame_acc_info = banking_api.get_minigame_account_info(uid)
                if minigame_acc_info:
                    account_number = minigame_acc_info.get('account_number')
                    branch_code = minigame_acc_info.get('branch_code')
                    if account_number and branch_code:
                        banking_api.deposit_by_account(account_number, branch_code, amount)
            except Exception:
                # 個別の入金失敗はログに留め、処理は続行
                pass
        
        # 手数料をミニゲーム運営用口座に振り込む
        if fee > 0:
            try:
                fee_account = banking_api.get_minigame_fee_account()
                banking_api.deposit_by_account(
                    fee_account['account_number'],
                    fee_account['branch_num'],
                    fee
                )
            except Exception as e:
                # 手数料の入金失敗はログに記録
                print(f"[Minigames] Failed to deposit fee to minigame account: {e}")
    except Exception:
        pass

    try:
        bubble = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "じゃんけん 結果", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": f"参加者: {n}名  合計参加費: {n * session.min_balance} JPY", "size": "xs", "color": "#888888"}
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "box", "layout": "vertical", "contents": flex_players}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "separator", "margin": "md"},
                    {"type": "box", "layout": "baseline", "contents": [
                        {"type": "text", "text": f"手数料合計: {fee} JPY", "size": "sm", "color": "#888888", "flex": 6},
                        {"type": "text", "text": "(収支は賞金-参加費-手数料分)", "size": "xs", "color": "#aaaaaa", "flex": 6}
                    ]}
                ]
            }
        }

        flex_message = FlexSendMessage(alt_text="じゃんけんの結果", contents=bubble)
        line_bot_api.push_message(group_id, flex_message)
    except Exception:
        pass

    group.current_game = None
