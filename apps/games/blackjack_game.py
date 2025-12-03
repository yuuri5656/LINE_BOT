"""
ブラックジャックゲームロジック
"""
import random
from typing import List, Dict, Tuple


# カードの絵文字マッピング
CARD_EMOJIS = {
    'spades': {
        'A': '🂡', '2': '🂢', '3': '🂣', '4': '🂤', '5': '🂥',
        '6': '🂦', '7': '🂧', '8': '🂨', '9': '🂩', '10': '🂪',
        'J': '🂫', 'Q': '🂭', 'K': '🂮'
    },
    'hearts': {
        'A': '🂱', '2': '🂲', '3': '🂳', '4': '🂴', '5': '🂵',
        '6': '🂶', '7': '🂷', '8': '🂸', '9': '🂹', '10': '🂺',
        'J': '🂻', 'Q': '🂽', 'K': '🂾'
    },
    'diamonds': {
        'A': '🃁', '2': '🃂', '3': '🃃', '4': '🃄', '5': '🃅',
        '6': '🃆', '7': '🃇', '8': '🃈', '9': '🃉', '10': '🃊',
        'J': '🃋', 'Q': '🃍', 'K': '🃎'
    },
    'clubs': {
        'A': '🃑', '2': '🃒', '3': '🃓', '4': '🃔', '5': '🃕',
        '6': '🃖', '7': '🃗', '8': '🃘', '9': '🃙', '10': '🃚',
        'J': '🃛', 'Q': '🃝', 'K': '🃞'
    }
}


def create_deck() -> List[Dict]:
    """
    52枚のカードデッキを生成してシャッフル

    Returns:
        List[Dict]: シャッフルされたデッキ
    """
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    deck = []
    for suit in suits:
        for rank in ranks:
            # 基本値の設定
            if rank in ['J', 'Q', 'K']:
                value = 10
            elif rank == 'A':
                value = 11  # 初期値は11、後で調整
            else:
                value = int(rank)

            card = {
                'suit': suit,
                'rank': rank,
                'value': value,
                'emoji': CARD_EMOJIS[suit][rank]
            }
            deck.append(card)

    # シャッフル
    random.shuffle(deck)
    return deck


def calculate_hand_value(hand: List[Dict]) -> int:
    """
    手札の合計値を計算（Aの1/11を自動最適化）

    Args:
        hand: 手札のリスト

    Returns:
        int: 手札の合計値
    """
    total = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['rank'] == 'A')

    # Aを11として計算してバーストする場合、1に変換
    while total > 21 and aces > 0:
        total -= 10  # A を 11 → 1 に変更（差分は10）
        aces -= 1

    return total


def is_blackjack(hand: List[Dict]) -> bool:
    """
    ブラックジャック判定（最初の2枚でAと10点札）

    Args:
        hand: 手札のリスト

    Returns:
        bool: ブラックジャックかどうか
    """
    if len(hand) != 2:
        return False

    values = sorted([card['value'] for card in hand])
    ranks = [card['rank'] for card in hand]

    # Aと10点札の組み合わせ
    return 'A' in ranks and any(r in ['10', 'J', 'Q', 'K'] for r in ranks)


def is_bust(hand: List[Dict]) -> bool:
    """
    バースト判定（合計値が21を超える）

    Args:
        hand: 手札のリスト

    Returns:
        bool: バーストかどうか
    """
    return calculate_hand_value(hand) > 21


def deal_initial_cards(deck: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    初期カードを配布（プレイヤー2枚、ディーラー2枚）

    Args:
        deck: カードデッキ

    Returns:
        Tuple[List[Dict], List[Dict], List[Dict]]: (プレイヤー手札, ディーラー手札, 残りデッキ)
    """
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    return player_hand, dealer_hand, deck


def hit_card(hand: List[Dict], deck: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    1枚カードを引く

    Args:
        hand: 現在の手札
        deck: カードデッキ

    Returns:
        Tuple[List[Dict], List[Dict]]: (更新された手札, 残りデッキ)
    """
    if len(deck) > 0:
        hand.append(deck.pop())
    return hand, deck


def dealer_play(dealer_hand: List[Dict], deck: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    ディーラーのプレイ（17以上になるまでヒット）

    Args:
        dealer_hand: ディーラーの手札
        deck: カードデッキ

    Returns:
        Tuple[List[Dict], List[Dict]]: (最終手札, 残りデッキ)
    """
    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand, deck = hit_card(dealer_hand, deck)

    return dealer_hand, deck


def calculate_winner(player_hand: List[Dict], dealer_hand: List[Dict],
                     bet_amount: int, is_doubled: bool = False) -> Dict:
    """
    勝敗判定と配当計算

    Args:
        player_hand: プレイヤーの手札
        dealer_hand: ディーラーの手札
        bet_amount: ベット額
        is_doubled: ダブルダウンしたか

    Returns:
        Dict: {
            'result': str,  # 'blackjack', 'win', 'lose', 'push', 'bust'
            'player_total': int,
            'dealer_total': int,
            'payout': int,  # 配当額（ベット額を含む）
            'message': str
        }
    """
    player_total = calculate_hand_value(player_hand)
    dealer_total = calculate_hand_value(dealer_hand)

    player_bj = is_blackjack(player_hand) and not is_doubled  # ダブルダウン後はBJにならない
    dealer_bj = is_blackjack(dealer_hand)
    player_bust = is_bust(player_hand)
    dealer_bust = is_bust(dealer_hand)

    result = {
        'player_total': player_total,
        'dealer_total': dealer_total,
        'payout': 0,
        'result': 'lose',
        'message': ''
    }

    # プレイヤーバースト
    if player_bust:
        result['result'] = 'bust'
        result['payout'] = 0
        result['message'] = 'バースト！ディーラーの勝ち'
        return result

    # ディーラーバースト
    if dealer_bust:
        result['result'] = 'win'
        result['payout'] = bet_amount * 2  # 2倍配当
        result['message'] = 'ディーラーがバースト！あなたの勝ち'
        return result

    # 両者ブラックジャック
    if player_bj and dealer_bj:
        result['result'] = 'push'
        result['payout'] = bet_amount  # ベット額返金
        result['message'] = '両者ブラックジャック！引き分け'
        return result

    # プレイヤーブラックジャック
    if player_bj:
        result['result'] = 'blackjack'
        result['payout'] = int(bet_amount * 2.5)  # 2.5倍配当
        result['message'] = 'ブラックジャック！2.5倍配当'
        return result

    # ディーラーブラックジャック
    if dealer_bj:
        result['result'] = 'lose'
        result['payout'] = 0
        result['message'] = 'ディーラーがブラックジャック！'
        return result

    # 通常の勝敗判定
    if player_total > dealer_total:
        result['result'] = 'win'
        result['payout'] = bet_amount * 2  # 2倍配当
        result['message'] = 'あなたの勝ち！'
    elif player_total < dealer_total:
        result['result'] = 'lose'
        result['payout'] = 0
        result['message'] = 'ディーラーの勝ち'
    else:
        result['result'] = 'push'
        result['payout'] = bet_amount  # ベット額返金
        result['message'] = '引き分け（プッシュ）'

    return result


def can_double_down(player_hand: List[Dict], chip_balance: int, bet_amount: int) -> bool:
    """
    ダブルダウン可能かチェック

    Args:
        player_hand: プレイヤーの手札
        chip_balance: チップ残高
        bet_amount: 現在のベット額

    Returns:
        bool: ダブルダウン可能か
    """
    # 最初の2枚のみ、かつベット額を倍にできる残高がある
    return len(player_hand) == 2 and chip_balance >= bet_amount


def process_double_down(player_hand: List[Dict], deck: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    ダブルダウン処理（1枚だけ引いて自動スタンド）

    Args:
        player_hand: プレイヤーの手札
        deck: カードデッキ

    Returns:
        Tuple[List[Dict], List[Dict]]: (更新された手札, 残りデッキ)
    """
    return hit_card(player_hand, deck)
