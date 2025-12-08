"""
ブラックジャックゲームロジック
"""
import random
from typing import List, Dict, Tuple


# カードの画像URLマッピング（chicodeza.comのトランプイラスト）
CARD_IMAGES = {
    'spades': {
        'A': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust1.png',
        '2': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust2.png',
        '3': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust3.png',
        '4': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust4.png',
        '5': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust5.png',
        '6': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust6.png',
        '7': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust7.png',
        '8': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust8.png',
        '9': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust9.png',
        '10': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust10.png',
        'J': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust11.png',
        'Q': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust12.png',
        'K': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust13.png'
    },
    'clubs': {
        'A': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust14.png',
        '2': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust15.png',
        '3': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust16.png',
        '4': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust17.png',
        '5': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust18.png',
        '6': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust19.png',
        '7': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust20.png',
        '8': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust21.png',
        '9': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust22.png',
        '10': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust23.png',
        'J': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust24.png',
        'Q': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust25.png',
        'K': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust26.png'
    },
    'diamonds': {
        'A': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust27.png',
        '2': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust28.png',
        '3': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust29.png',
        '4': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust30.png',
        '5': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust31.png',
        '6': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust32.png',
        '7': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust33.png',
        '8': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust34.png',
        '9': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust35.png',
        '10': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust36.png',
        'J': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust37.png',
        'Q': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust38.png',
        'K': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust39.png'
    },
    'hearts': {
        'A': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust40.png',
        '2': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust41.png',
        '3': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust42.png',
        '4': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust43.png',
        '5': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust44.png',
        '6': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust45.png',
        '7': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust46.png',
        '8': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust47.png',
        '9': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust48.png',
        '10': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust49.png',
        'J': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust50.png',
        'Q': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust51.png',
        'K': 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust52.png'
    }
}

# 裏面の画像URL
CARD_BACK_IMAGE = 'https://chicodeza.com/wordpress/wp-content/uploads/torannpu-illust54.png'


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
                'image_url': CARD_IMAGES[suit][rank]
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
        # payout はベット額を含む総返却額（元のベット + 純利益）
        # 通常勝利の純利益はベット額と同額なので、総返却は2倍
        result['payout'] = bet_amount * 2
        result['message'] = 'ディーラーがバースト！あなたの勝ち'
        return result

    # 両者ブラックジャック
    if player_bj and dealer_bj:
        result['result'] = 'push'
        # 引き分けはベット額を返却する
        result['payout'] = bet_amount
        result['message'] = '両者ブラックジャック！引き分け'
        return result

    # プレイヤーブラックジャック
    if player_bj:
        result['result'] = 'blackjack'
        # ブラックジャックは純利益が1.5倍（ベットの150%）、
        # 総返却額は元のベット + 1.5倍 = 2.5倍
        result['payout'] = int(bet_amount * 2.5)
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
        # 勝利時は純利益がベット額と同額のため、総返却は2倍
        result['payout'] = bet_amount * 2
        result['message'] = 'あなたの勝ち！'
    elif player_total < dealer_total:
        result['result'] = 'lose'
        result['payout'] = 0
        result['message'] = 'ディーラーの勝ち'
    else:
        result['result'] = 'push'
        # 引き分けはベット額を返却
        result['payout'] = bet_amount
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
