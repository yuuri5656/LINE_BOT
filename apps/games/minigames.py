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
from typing import Dict, List
from datetime import datetime
from enum import Enum
from linebot.models import TextSendMessage, FlexSendMessage
from apps.utilities.timezone_utils import now_jst
from apps.banking.api import banking_api
from apps.banking.chip_service import (
    get_chip_balance,
    batch_lock_chips,
    distribute_chips
)

# じゃんけんゲームの最大再戦回数
MAX_ROUNDS = 6


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


def create_round_result_flex_message(round_num, all_hands, eliminated, remaining_players):
    """
    各ラウンドの結果を表示するFlexMessage

    Args:
        round_num: ラウンド番号
        all_hands: 全プレイヤーの手 {user_id: {'name': str, 'hand': str}}
        eliminated: 脱落者リスト [{'user_id', 'display_name', 'hand'}]
        remaining_players: 残存プレイヤー数
    """
    # 手の絵文字マッピング
    hand_emoji = {
        "グー": "✊",
        "チョキ": "✌️",
        "パー": "✋"
    }

    # 全プレイヤーの手を表示
    hand_contents = []
    for uid, info in all_hands.items():
        emoji = hand_emoji.get(info['hand'], "❓")
        is_eliminated = any(e['user_id'] == uid for e in eliminated)
        color = "#FF5252" if is_eliminated else "#111111"

        hand_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{emoji} {info['name']}",
                    "size": "sm",
                    "color": color,
                    "weight": "bold" if is_eliminated else "regular",
                    "flex": 3,
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": info['hand'],
                    "size": "sm",
                    "color": color,
                    "align": "end",
                    "flex": 1
                }
            ],
            "margin": "md"
        })

    # 結果メッセージ
    if eliminated:
        eliminated_names = "、".join([e['display_name'] for e in eliminated])
        result_text = f"❌ 脱落: {eliminated_names}"
        result_color = "#FF5252"
    else:
        result_text = "あいこでしょ！"
        result_color = "#FFA726"

    return FlexSendMessage(
        alt_text=f"第{round_num}ラウンド結果",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"第{round_num}ラウンド",
                        "size": "xl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF"
                    }
                ],
                "backgroundColor": "#42A5F5",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "出された手",
                        "size": "md",
                        "weight": "bold",
                        "color": "#111111",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": hand_contents,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": result_text,
                        "size": "lg",
                        "weight": "bold",
                        "color": result_color,
                        "align": "center",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": f"残り{remaining_players}人",
                        "size": "sm",
                        "color": "#666666",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "spacing": "sm",
                "paddingAll": "20px"
            }
        }
    )


def create_winner_result_flex_message(winner_info, prize_info, round_history):
    """
    最終結果（勝者）を表示するFlexMessage

    Args:
        winner_info: {'user_id', 'display_name', 'hand'}
        prize_info: {'total_pot', 'fee', 'prize', 'fee_rate'}
        round_history: 全ラウンド履歴 [{'round', 'hands': {user_id: {'name', 'hand'}}, 'eliminated': [...]}]
    """
    hand_emoji = {
        "グー": "✊",
        "チョキ": "✌️",
        "パー": "✋"
    }

    winner_emoji = hand_emoji.get(winner_info['hand'], "❓")
    fee_rate_percent = prize_info['fee_rate'] * 100

    # ラウンド履歴を簡潔に表示
    history_contents = []
    for hist in round_history:
        round_num = hist['round']
        eliminated = hist.get('eliminated', [])
        if eliminated:
            elim_names = "、".join([e['display_name'] for e in eliminated])
            history_text = f"R{round_num}: {elim_names} 脱落"
        else:
            history_text = f"R{round_num}: あいこ"

        history_contents.append({
            "type": "text",
            "text": history_text,
            "size": "xs",
            "color": "#666666",
            "margin": "sm"
        })

    return FlexSendMessage(
        alt_text="じゃんけん結果",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏆",
                        "size": "xxl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF"
                    },
                    {
                        "type": "text",
                        "text": "じゃんけん結果",
                        "size": "xl",
                        "align": "center",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#FFA726",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🥇 優勝",
                        "size": "lg",
                        "weight": "bold",
                        "color": "#FFD700",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{winner_emoji} {winner_info['display_name']}",
                                "size": "md",
                                "weight": "bold",
                                "color": "#111111",
                                "flex": 3,
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": winner_info['hand'],
                                "size": "md",
                                "color": "#111111",
                                "align": "end",
                                "flex": 1
                            }
                        ],
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
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "総額:",
                                        "size": "sm",
                                        "color": "#999999",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{prize_info['total_pot']}枚",
                                        "size": "sm",
                                        "color": "#111111",
                                        "margin": "sm"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "手数料:",
                                        "size": "sm",
                                        "color": "#999999",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{prize_info['fee']}枚 ({fee_rate_percent:.1f}%)",
                                        "size": "sm",
                                        "color": "#FF5252",
                                        "margin": "sm"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "獲得賞金:",
                                        "size": "sm",
                                        "color": "#999999",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{prize_info['prize']}枚",
                                        "size": "md",
                                        "color": "#4CAF50",
                                        "weight": "bold",
                                        "margin": "sm"
                                    }
                                ],
                                "margin": "md"
                            }
                        ],
                        "margin": "xl"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "ラウンド履歴",
                        "size": "sm",
                        "weight": "bold",
                        "color": "#111111",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": history_contents if history_contents else [
                            {
                                "type": "text",
                                "text": "1ラウンドで決着",
                                "size": "xs",
                                "color": "#666666"
                            }
                        ],
                        "margin": "sm"
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
    # 再戦管理用フィールド
    round_count: int = 0  # 現在のラウンド数
    eliminated_players: List[Dict] = field(default_factory=list)  # 脱落者履歴: [{'user_id', 'display_name', 'hand', 'round'}]
    round_history: List[Dict] = field(default_factory=list)  # 各ラウンドの全員の手: [{'round', 'hands': {user_id: hand}}]

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

def check_chip_balance(user_id, min_chips):
    """
    ユーザーのチップ残高が必要量を満たしているか確認する。
    """
    try:
        balance_info = get_chip_balance(user_id)
        # get_chip_balance は辞書を返すので、available キーを使用
        return balance_info.get('available', 0) >= min_chips
    except Exception:
        return False


def calculate_winner_takes_all(total_players: int, bet_amount: int):
    """
    勝者総取り方式の賞金計算。
    手数料は全体の約10%で、10の倍数に丸め込まれる。

    Args:
        total_players: 参加者総数
        bet_amount: 1人あたりの参加費

    Returns:
        dict: {
            'total_pot': 総額,
            'fee': 手数料,
            'prize': 勝者への賞金,
            'fee_rate': 実際の手数料率
        }
    """
    total_pot = total_players * bet_amount
    # 手数料を10%として計算し、10の倍数に丸め込む
    fee_raw = total_pot * 0.1
    fee = round(fee_raw / 10) * 10
    prize = total_pot - fee
    fee_rate = fee / total_pot if total_pot > 0 else 0.0

    return {
        'total_pot': total_pot,
        'fee': fee,
        'prize': prize,
        'fee_rate': fee_rate
    }


def fixed_prize_distribution(bets, fee_rate=0.1):
    """
    小規模（2～5人）向けの固定分配方式。
    1位圧倒的、下位にも少額分配。
    ※この関数は後方互換性のために残していますが、じゃんけんゲームでは使用しません。
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

    # チップ残高の確認
    if not check_chip_balance(user_id, group.current_game.min_balance):
        return f"チップ残高が不足しています（必要: {group.current_game.min_balance}枚）。\n\nショップでチップを購入してください。\nコマンド: ?ショップ"

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
    session.start_time = now_jst()
    session.deadline = session.start_time + timedelta(seconds=timeout_seconds)

    # 参加費をチップから一括ロック（バッチ処理）
    user_ids = list(session.players.keys())
    lock_data = [
        {
            'user_id': uid,
            'amount': session.min_balance,
            'game_session_id': f"rps_game_{group_id}_round{session.round_count}"
        }
        for uid in user_ids
    ]
    lock_result = batch_lock_chips(lock_data)

    if not lock_result['success']:
        # 全員失敗（トランザクションロールバック済み）
        session.state = GameState.RECRUITING
        error_msg = lock_result.get('error', 'チップのロックに失敗しました')
        try:
            msg = f"参加費のロックに失敗しました。\n詳細: {error_msg}"
            if reply_token:
                line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
            else:
                line_bot_api.push_message(group_id, TextSendMessage(text=msg))
        except Exception:
            pass
        return "参加費のロックに失敗しました。"

    # 成功したユーザーのみを残す
    locked = lock_result.get('locked', [])
    failed = lock_result.get('failed', [])

    # ロック失敗したユーザーは参加者リストから除外
    for uid in failed:
        if uid in session.players:
            del session.players[uid]

    # デバッグ出力: ロック状況と残存プレイヤー
    try:
        print(f"start_game_session: group={group_id} locked={locked} failed={failed} remaining_players={list(session.players.keys())}")
    except Exception:
        pass

    # 参加者不足チェック（テスト用: 1人でも開始可能）
    remaining = list(session.players.keys())
    if len(remaining) < 1:  # ←元は <2
        # バッチ処理で一括ロック済みなので、返金は不要（トランザクションがロールバック済み）
        # セッションを中止してグループに通知
        try:
            msg = "参加者がいないため、ゲームを開始できません。"
            if reply_token:
                line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
            else:
                line_bot_api.push_message(group_id, TextSendMessage(text=msg))
        except Exception as e:
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

    # ロックできなかったユーザーを通知
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
    """
    じゃんけんゲームのラウンド終了処理（脱落制・勝者総取り方式）
    """
    from threading import Timer

    group = manager.groups.get(group_id)
    if not group or not group.current_game:
        return

    session = group.current_game
    print(f"finish_game_session: group={group_id} round={session.round_count} state={session.state} players={list(session.players.keys())}")

    # ラウンド数をインクリメント
    session.round_count += 1
    current_round = session.round_count

    # 現在のプレイヤーリスト
    active_players = list(session.players.values())

    # 全員の手を収集
    current_hands = {}
    for p in active_players:
        hand = p.data if p.data else None
        current_hands[p.user_id] = {
            'name': p.display_name,
            'hand': hand if hand else "未提出"
        }

    # 未提出者の処理（タイムアウト扱い）
    timeout_players = [p for p in active_players if not p.data]

    # 提出済みプレイヤーのみで判定
    submitted_players = [p for p in active_players if p.data]

    if len(submitted_players) < 1:
        # 全員未提出の場合はゲーム終了（返金処理）
        session.state = GameState.FINISHED
        try:
            line_bot_api.push_message(group_id, TextSendMessage(
                text="全員が手を提出しなかったため、ゲームを終了し参加費を返却します。"
            ))
        except Exception:
            pass

        # 返金処理
        total_players = len(active_players) + len(session.eliminated_players)
        distributions = {
            p.user_id: {
                'locked': session.min_balance,
                'payout': session.min_balance  # 全額返金
            } for p in active_players
        }

        try:
            distribute_chips(distributions, f"rps_game_{group_id}_round{current_round}")
        except Exception as e:
            print(f"[Minigames] Error in refund: {e}")

        group.current_game = None
        return

    # あいこ判定関数
    def check_draw(players_list):
        """あいこかどうかを判定"""
        if len(players_list) < 2:
            return False

        hands = [p.data for p in players_list]
        unique_hands = set(hands)

        if len(players_list) == 2:
            # 2人の場合：同じ手ならあいこ
            return len(unique_hands) == 1
        else:
            # 3人以上の場合：グー・チョキ・パー全種類揃う OR 全員同じ手
            return len(unique_hands) == 3 or len(unique_hands) == 1

    # 脱落者判定関数
    def find_eliminated(players_list):
        """最弱の手のプレイヤーを特定"""
        hand_groups = {"グー": [], "チョキ": [], "パー": []}
        for p in players_list:
            if p.data in hand_groups:
                hand_groups[p.data].append(p)

        # 存在する手の種類を確認
        existing_hands = [h for h in ["グー", "チョキ", "パー"] if hand_groups[h]]

        if len(existing_hands) == 3:
            # 3種類揃った場合はあいこ（この関数は呼ばれないはず）
            return []
        elif len(existing_hands) == 2:
            # 2種類の場合、負ける方を特定
            if "グー" in existing_hands and "パー" in existing_hands:
                return hand_groups["グー"]  # パーに負ける
            elif "チョキ" in existing_hands and "グー" in existing_hands:
                return hand_groups["チョキ"]  # グーに負ける
            elif "パー" in existing_hands and "チョキ" in existing_hands:
                return hand_groups["パー"]  # チョキに負ける
        elif len(existing_hands) == 1:
            # 全員同じ手（あいこ、この関数は呼ばれないはず）
            return []

        return []

    # あいこ判定
    is_draw = check_draw(submitted_players)

    # タイムアウト者を脱落扱いに
    if timeout_players:
        for p in timeout_players:
            session.eliminated_players.append({
                'user_id': p.user_id,
                'display_name': p.display_name,
                'hand': '未提出',
                'round': current_round
            })
            if p.user_id in session.players:
                del session.players[p.user_id]

        # タイムアウト者除外後に再判定
        active_players = list(session.players.values())
        submitted_players = [p for p in active_players if p.data]

    # ラウンド履歴に記録
    round_eliminated = []

    if is_draw:
        # あいこの場合
        print(f"[Minigames] Round {current_round}: Draw")

        # ラウンド履歴に記録
        session.round_history.append({
            'round': current_round,
            'hands': current_hands,
            'eliminated': []
        })

        # 最大ラウンド数チェック
        if current_round >= MAX_ROUNDS:
            # 上限到達：参加費返却
            session.state = GameState.FINISHED

            try:
                line_bot_api.push_message(group_id, create_round_result_flex_message(
                    current_round, current_hands, [], len(submitted_players)
                ))
                line_bot_api.push_message(group_id, TextSendMessage(
                    text=f"🤝 {MAX_ROUNDS}回あいこが続いたため、ゲームを終了し参加費を全額返却します！"
                ))
            except Exception as e:
                print(f"[Minigames] Error sending draw limit message: {e}")

            # 返金処理
            total_players = len(active_players) + len(session.eliminated_players)
            distributions = {}

            # 残存プレイヤーに返金
            for p in active_players:
                distributions[p.user_id] = {
                    'locked': session.min_balance,
                    'payout': session.min_balance
                }

            # 脱落者にも返金
            for elim in session.eliminated_players:
                distributions[elim['user_id']] = {
                    'locked': session.min_balance,
                    'payout': session.min_balance
                }

            try:
                distribute_chips(distributions, f"rps_game_{group_id}_round{current_round}")
            except Exception as e:
                print(f"[Minigames] Error in refund: {e}")

            group.current_game = None
            return

        # 再戦処理
        # プレイヤーの手をクリア
        for p in active_players:
            p.data = ""

        # 状態をIN_PROGRESSに戻す
        session.state = GameState.IN_PROGRESS

        # ラウンド結果を送信
        try:
            line_bot_api.push_message(group_id, create_round_result_flex_message(
                current_round, current_hands, [], len(submitted_players)
            ))
            line_bot_api.push_message(group_id, TextSendMessage(
                text=f"あいこでしょ！次のラウンドを開始します（残り{len(submitted_players)}人）"
            ))
        except Exception as e:
            print(f"[Minigames] Error sending draw message: {e}")

        # タイマー再設定
        timeout_seconds = 30

        def _finish():
            try:
                finish_game_session(group_id, line_bot_api)
            except Exception as e:
                print(f"[Minigames] Error in timer finish: {e}")

        if session.timer:
            try:
                session.timer.cancel()
            except Exception:
                pass

        timer = Timer(timeout_seconds, _finish)
        session.timer = timer
        timer.daemon = True
        timer.start()

        return

    # あいこでない場合：脱落者を特定
    eliminated = find_eliminated(submitted_players)

    for p in eliminated:
        round_eliminated.append({
            'user_id': p.user_id,
            'display_name': p.display_name,
            'hand': p.data
        })
        session.eliminated_players.append({
            'user_id': p.user_id,
            'display_name': p.display_name,
            'hand': p.data,
            'round': current_round
        })
        if p.user_id in session.players:
            del session.players[p.user_id]

    # ラウンド履歴に記録
    session.round_history.append({
        'round': current_round,
        'hands': current_hands,
        'eliminated': round_eliminated
    })

    # 残存プレイヤー確認
    remaining_players = list(session.players.values())

    print(f"[Minigames] Round {current_round}: Eliminated={len(eliminated)}, Remaining={len(remaining_players)}")

    # ラウンド結果を送信
    try:
        line_bot_api.push_message(group_id, create_round_result_flex_message(
            current_round, current_hands, round_eliminated, len(remaining_players)
        ))
    except Exception as e:
        print(f"[Minigames] Error sending round result: {e}")

    if len(remaining_players) == 1:
        # 勝者決定
        session.state = GameState.FINISHED
        winner = remaining_players[0]

        # 賞金計算
        total_players = len(session.eliminated_players) + 1  # 脱落者 + 勝者
        prize_info = calculate_winner_takes_all(total_players, session.min_balance)

        # チップ分配：payout はベット返却を含む総払戻
        distributions = {}

        # 勝者に総賞金（ベット返却を含む総払戻として扱う）
        distributions[winner.user_id] = {
            'locked': session.min_balance,
            'payout': int(prize_info['prize'])
        }

        # 敗者は0
        for elim in session.eliminated_players:
            distributions[elim['user_id']] = {
                'locked': session.min_balance,
                'payout': 0
            }

        try:
            result = distribute_chips(distributions, f"rps_game_{group_id}_round{current_round}")
            if result.get('success'):
                print(f"[Minigames] Successfully distributed chips to winner: {winner.user_id}")
            else:
                print(f"[Minigames] Failed to distribute chips: {result.get('error')}")
        except Exception as e:
            print(f"[Minigames] Error in chip distribution: {e}")

        # 手数料をミニゲーム運営口座に振り込み
        try:
            from apps.banking.bank_service import transfer_funds
            from decimal import Decimal
            
            fee_amount = Decimal(str(prize_info['fee']))
            
            # ミニゲーム運営口座に手数料を振り込む
            # 参加者全員の口座から集めた参加費の総額から手数料を計算して転送
            result = transfer_funds(
                from_account_number='6291119',  # ミニゲーム手数料受取口座（運営元）
                to_account_number='6291119',    # 実際の手数料はロック&ロック解除で処理されるため、
                amount=fee_amount,              # ここでは記録のための転送（実装実現度により調整）
                currency='JPY',
                description=f'ゲーム手数料 ({total_players}人対戦)'
            )
            print(f"[Minigames] Game fee transferred: amount={fee_amount}, tx_id={result['transaction_id']}")
        except Exception as e:
            # 手数料転送失敗時は警告のみで処理を続行
            print(f"[Minigames] Warning: Failed to transfer game fee: {e}")

        # 最終結果FlexMessage送信
        winner_info = {
            'user_id': winner.user_id,
            'display_name': winner.display_name,
            'hand': winner.data
        }

        try:
            line_bot_api.push_message(group_id, create_winner_result_flex_message(
                winner_info, prize_info, session.round_history
            ))
        except Exception as e:
            print(f"[Minigames] Error sending winner result: {e}")

        # セッションクリア
        group.current_game = None
        # 勝者決定後は即座にreturnして、次のラウンド処理に進まないようにする
        return

    if len(remaining_players) > 1:
        # まだ複数人残っている：再戦
        # プレイヤーの手をクリア
        for p in remaining_players:
            p.data = ""

        # 状態をIN_PROGRESSに戻す
        session.state = GameState.IN_PROGRESS

        # 次のラウンド開始メッセージ
        try:
            line_bot_api.push_message(group_id, TextSendMessage(
                text=f"次のラウンドを開始します！残り{len(remaining_players)}人"
            ))
        except Exception as e:
            print(f"[Minigames] Error sending next round message: {e}")

        # タイマー再設定
        timeout_seconds = 30

        def _finish():
            try:
                finish_game_session(group_id, line_bot_api)
            except Exception as e:
                print(f"[Minigames] Error in timer finish: {e}")

        if session.timer:
            try:
                session.timer.cancel()
            except Exception:
                pass

        timer = Timer(timeout_seconds, _finish)
        session.timer = timer
        timer.daemon = True
        timer.start()

        return

    else:
        # 残り0人（全員脱落）：エラー処理
        session.state = GameState.FINISHED
        try:
            line_bot_api.push_message(group_id, TextSendMessage(
                text="全員が脱落したため、ゲームを終了します。"
            ))
        except Exception:
            pass
        group.current_game = None
        return
