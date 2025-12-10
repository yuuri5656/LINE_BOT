"""
ミニゲーム用チップ管理サービス
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
import datetime
from typing import Optional, Dict, List
from apps.utilities.timezone_utils import now_jst

from apps.banking.main_bank_system import (
    SessionLocal,
    Account,
    Branch,
    MinigameChip,
    ChipTransaction,
    ShopPaymentAccount,
)


def get_chip_balance(user_id: str) -> Dict:
    """
    ユーザーのチップ残高を取得

    Returns:
        {
            'base_balance': int,
            'bonus_balance': int,
            'locked_base_balance': int,
            'locked_bonus_balance': int,
            'available_base': int,  # 基本チップの利用可能枚数（換金/転送可能）
            'available_bonus': int   # ボーナスチップの利用可能枚数（使用のみ）
        }
    """
    db = SessionLocal()
    try:
        chip_acc = db.execute(
            select(MinigameChip).filter_by(user_id=user_id)
        ).scalars().first()

        if not chip_acc:
            return {
                'base_balance': 0,
                'bonus_balance': 0,
                'locked_base_balance': 0,
                'locked_bonus_balance': 0,
                'available_base': 0,
                'available_bonus': 0
            }

        base_balance = int(chip_acc.base_balance)
        bonus_balance = int(chip_acc.bonus_balance)
        locked_base = int(chip_acc.locked_base_balance)
        locked_bonus = int(chip_acc.locked_bonus_balance)

        return {
            'base_balance': base_balance,
            'bonus_balance': bonus_balance,
            'locked_base_balance': locked_base,
            'locked_bonus_balance': locked_bonus,
            'available_base': base_balance - locked_base,
            'available_bonus': bonus_balance - locked_bonus
        }
    finally:
        db.close()


def create_chip_account(user_id: str) -> Dict:
    """チップアカウントを作成（初回のみ）"""
    db = SessionLocal()
    try:
        with db.begin():
            existing = db.execute(
                select(MinigameChip).filter_by(user_id=user_id)
            ).scalars().first()

            if existing:
                return {'success': True, 'message': '既にチップアカウントが存在します'}

            chip_acc = MinigameChip(
                user_id=user_id,
                balance=Decimal('0'),
                locked_balance=Decimal('0'),
                base_balance=Decimal('0'),
                bonus_balance=Decimal('0'),
                locked_base_balance=Decimal('0'),
                locked_bonus_balance=Decimal('0')
            )
            db.add(chip_acc)
            db.flush()

        return {'success': True, 'message': 'チップアカウントを作成しました'}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def purchase_chips(user_id: str, base_amount: int, bonus_amount: int, account_number: str, branch_code: str, price: Decimal) -> Dict:
    """
    ショップ支払い用口座からチップを購入

    Args:
        user_id: ユーザーID
        base_amount: 基本チップ枚数
        bonus_amount: ボーナスチップ枚数
        account_number: 支払い口座番号
        branch_code: 支払い口座の支店コード
        price: 商品価格（データベースから取得）

    Returns:
        {'success': bool, 'new_base_balance': int, 'new_bonus_balance': int, 'error': str (optional)}
    """
    from apps.banking.bank_service import withdraw_by_account_number, deposit_by_account_number
    from apps.shop.shop_service import get_shop_operations_account

    db = SessionLocal()

    try:
        # ショップ運営口座情報を取得
        shop_account = get_shop_operations_account()

        # 口座から引き落とし（摘要と相手口座を記録）
        try:
            withdraw_by_account_number(
                account_number,
                branch_code,
                price,
                'JPY',
                description=f'チップ購入 {base_amount + bonus_amount}枚',
                other_account_info=f"{shop_account['branch_num']}-{shop_account['account_number']}"
            )
        except Exception as e:
            return {'success': False, 'error': f'口座からの引き落としに失敗しました: {str(e)}'}

        # ショップ運営口座に売上を入金
        try:
            deposit_by_account_number(
                shop_account['account_number'],
                shop_account['branch_num'],
                price,
                'JPY',
                description=f'チップ販売',
                other_account_info=f"{branch_code}-{account_number}"
            )
        except Exception as e:
            # 売上入金失敗時は引き落としを戻す処理が必要だが、
            # ここでは警告のみ（運営口座が存在しない等のエラー）
            print(f"[ChipService] Failed to deposit to shop operations account: {e}")
            # 必要に応じて引き落とし分を返金する処理を追加

        with db.begin():
            # チップ残高を増やす
            chip_acc = db.execute(
                select(MinigameChip).filter_by(user_id=user_id).with_for_update()
            ).scalars().first()

            if not chip_acc:
                chip_acc = MinigameChip(
                    user_id=user_id,
                    balance=Decimal('0'),
                    locked_balance=Decimal('0'),
                    base_balance=Decimal('0'),
                    bonus_balance=Decimal('0'),
                    locked_base_balance=Decimal('0'),
                    locked_bonus_balance=Decimal('0')
                )
                db.add(chip_acc)
                db.flush()

            base_amt = Decimal(str(base_amount))
            bonus_amt = Decimal(str(bonus_amount))
            
            # 新フィールドに追加
            chip_acc.base_balance += base_amt
            chip_acc.bonus_balance += bonus_amt
            
            # 互換性のため古いフィールドも同時に更新
            chip_acc.balance += base_amt + bonus_amt
            chip_acc.updated_at = now_jst()

            # 基本チップの取引履歴を記録
            if base_amount > 0:
                tx_base = ChipTransaction(
                    user_id=user_id,
                    amount=base_amt,
                    balance_after=chip_acc.base_balance,
                    type='purchase',
                    chip_type='base',
                    description=f'基本チップ{base_amount}枚を購入'
                )
                db.add(tx_base)

            # ボーナスチップの取引履歴を記録
            if bonus_amount > 0:
                tx_bonus = ChipTransaction(
                    user_id=user_id,
                    amount=bonus_amt,
                    balance_after=chip_acc.bonus_balance,
                    type='purchase',
                    chip_type='bonus',
                    description=f'ボーナスチップ{bonus_amount}枚を購入'
                )
                db.add(tx_bonus)
            
            db.flush()

            new_base_balance = int(chip_acc.base_balance)
            new_bonus_balance = int(chip_acc.bonus_balance)

        return {
            'success': True,
            'new_base_balance': new_base_balance,
            'new_bonus_balance': new_bonus_balance
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


def transfer_chips(from_user_id: str, to_user_id: str, amount: int) -> Dict:
    """
    ユーザー間でチップを送る
    ⚠️ 基本チップのみ転送可能。ボーナスチップは転送不可

    Returns:
        {'success': bool, 'new_base_balance': int, 'error': str (optional)}
    """
    db = SessionLocal()
    amt = Decimal(str(amount))

    try:
        with db.begin():
            # 送信者のチップアカウント
            from_acc = db.execute(
                select(MinigameChip).filter_by(user_id=from_user_id).with_for_update()
            ).scalars().first()

            if not from_acc:
                raise ValueError('チップ残高がありません')

            # ⚠️ 基本チップのみ転送可能
            available = from_acc.base_balance - from_acc.locked_base_balance
            if available < amt:
                raise ValueError(f'利用可能な基本チップが不足しています（必要: {amount}, 利用可能: {int(available)}）\n※ボーナスチップは転送できません')

            # 受信者のチップアカウント
            to_acc = db.execute(
                select(MinigameChip).filter_by(user_id=to_user_id).with_for_update()
            ).scalars().first()

            if not to_acc:
                to_acc = MinigameChip(
                    user_id=to_user_id,
                    balance=Decimal('0'),
                    locked_balance=Decimal('0'),
                    base_balance=Decimal('0'),
                    bonus_balance=Decimal('0'),
                    locked_base_balance=Decimal('0'),
                    locked_bonus_balance=Decimal('0')
                )
                db.add(to_acc)
                db.flush()

            # 転送（基本チップのみ）
            from_acc.base_balance -= amt
            from_acc.balance -= amt
            from_acc.updated_at = now_jst()

            to_acc.base_balance += amt
            to_acc.balance += amt
            to_acc.updated_at = now_jst()

            # 履歴記録
            tx_out = ChipTransaction(
                user_id=from_user_id,
                amount=-amt,
                balance_after=from_acc.base_balance,
                type='transfer_out',
                chip_type='base',
                related_user_id=to_user_id,
                description=f'{to_user_id}へ基本チップ{amount}枚送信'
            )
            tx_in = ChipTransaction(
                user_id=to_user_id,
                amount=amt,
                balance_after=to_acc.base_balance,
                type='transfer_in',
                chip_type='base',
                related_user_id=from_user_id,
                description=f'{from_user_id}から基本チップ{amount}枚受信'
            )
            db.add_all([tx_out, tx_in])
            db.flush()

            new_balance = int(from_acc.base_balance)

        return {
            'success': True,
            'new_base_balance': new_balance
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


def batch_lock_chips(locks: List[Dict]) -> Dict:
    """
    複数ユーザーのチップを一括ロック（ゲーム開始時）
    優先順: 基本チップ → ボーナスチップの順で消費

    Args:
        locks: [{'user_id': str, 'amount': int, 'game_session_id': str}, ...]
    """
    db = SessionLocal()
    completed = []
    failed = []

    try:
        with db.begin():
            for lock in locks:
                user_id = lock['user_id']
                amt = Decimal(str(lock['amount']))
                game_session_id = lock['game_session_id']

                try:
                    chip_acc = db.execute(
                        select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                    ).scalars().first()

                    if not chip_acc:
                        failed.append({'user_id': user_id, 'error': 'チップアカウントなし'})
                        continue

                    # 利用可能なチップを計算（基本 + ボーナス）
                    available_base = chip_acc.base_balance - chip_acc.locked_base_balance
                    available_bonus = chip_acc.bonus_balance - chip_acc.locked_bonus_balance
                    total_available = available_base + available_bonus

                    if total_available < amt:
                        failed.append({'user_id': user_id, 'error': f'チップ不足（必要:{lock["amount"]}, 利用可能:{int(total_available)}）'})
                        continue

                    # 優先順: 基本チップ → ボーナスチップ
                    if available_base >= amt:
                        # 基本チップのみで済む
                        chip_acc.locked_base_balance += amt
                        locked_type = 'base'
                    else:
                        # 基本チップ + ボーナスチップ
                        bonus_needed = amt - available_base
                        chip_acc.locked_base_balance += available_base
                        chip_acc.locked_bonus_balance += bonus_needed
                        locked_type = 'mixed'

                    chip_acc.updated_at = now_jst()

                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=-amt,
                        balance_after=chip_acc.base_balance + chip_acc.bonus_balance,
                        type='game_bet',
                        chip_type=locked_type,
                        game_session_id=game_session_id,
                        description=f'ゲーム参加費{lock["amount"]}枚'
                    )
                    db.add(tx)

                    completed.append(user_id)

                except Exception as e:
                    failed.append({'user_id': user_id, 'error': str(e)})

            # 全員成功が必要
            if failed:
                raise ValueError(f"{len(failed)}人のチップロックに失敗しました")

            db.flush()

        return {
            'success': True,
            'completed': completed,
            'failed': []
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'completed': [],
            'failed': failed if failed else [{'error': str(e)}]
        }
    finally:
        db.close()


def distribute_chips(distributions: Dict, game_session_id: str) -> Dict:
    """
    ゲーム終了時にチップを分配（ロック解除 + 賞金付与）

    Args:
        distributions: 2つのフォーマットをサポート
        
        フォーマット1（新）:
        {
            user_id: {
                'locked_base': int,   # ロックした基本チップ
                'locked_bonus': int,  # ロックしたボーナスチップ
                'payout': int         # 賞金額（純粋な獲得分、参加費は含まない）
            },
            ...
        }
        
        フォーマット2（旧・互換性）:
        {
            user_id: {
                'locked': int,   # ロック総額（基本+ボーナス）
                'payout': int    # 賞金額
            },
            ...
        }
        
        game_session_id: ゲームセッションID
    """
    db = SessionLocal()
    completed = []

    try:
        with db.begin():
            for user_id, dist in distributions.items():
                # フォーマットの判定
                if 'locked_base' in dist or 'locked_bonus' in dist:
                    # フォーマット1（新）
                    locked_base_amt = Decimal(str(dist.get('locked_base', 0)))
                    locked_bonus_amt = Decimal(str(dist.get('locked_bonus', 0)))
                else:
                    # フォーマット2（旧・互換性）- locked から自動判定
                    locked_total = Decimal(str(dist.get('locked', 0)))
                    # 優先順に基本チップから控除したと仮定
                    locked_base_amt = locked_total
                    locked_bonus_amt = Decimal('0')
                
                payout_amt = Decimal(str(dist['payout']))

                chip_acc = db.execute(
                    select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                ).scalars().first()

                if not chip_acc:
                    continue

                # ロック解除（ベット額を残高から引く）
                chip_acc.base_balance -= locked_base_amt
                chip_acc.locked_base_balance -= locked_base_amt
                
                chip_acc.bonus_balance -= locked_bonus_amt
                chip_acc.locked_bonus_balance -= locked_bonus_amt

                # 互換性のため古いフィールドも更新
                chip_acc.balance -= (locked_base_amt + locked_bonus_amt)
                chip_acc.locked_balance -= (locked_base_amt + locked_bonus_amt)

                # 賞金付与（基本チップとして）
                chip_acc.base_balance += payout_amt
                chip_acc.balance += payout_amt
                chip_acc.updated_at = now_jst()

                # 履歴記録
                if payout_amt > 0:
                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=payout_amt,
                        balance_after=chip_acc.base_balance,
                        type='game_win',
                        chip_type='base',
                        game_session_id=game_session_id,
                        description=f'ゲーム賞金{int(payout_amt)}枚獲得（基本チップ）'
                    )
                    db.add(tx)

                completed.append(user_id)

            db.flush()

        return {
            'success': True,
            'completed': completed
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


def redeem_chips(user_id: str, amount: int) -> Dict:
    """
    チップを換金（銀行口座に振り込み）
    ⚠️ 基本チップのみ換金可能。ボーナスチップは換金不可
    換金率: 1チップ = 12 JPY

    Args:
        user_id: ユーザーID
        amount: 換金するチップ枚数（基本チップのみ）

    Returns:
        {'success': bool, 'new_base_balance': int, 'amount_received': int, 'error': str (optional)}
    """
    from apps.banking.bank_service import deposit_by_account_number
    from apps.banking.api import banking_api

    db = SessionLocal()
    amt = Decimal(str(amount))

    try:
        # 支払い口座情報を取得（換金先口座）
        payment_acc = db.execute(
            select(ShopPaymentAccount).filter_by(user_id=user_id, is_active=True)
        ).scalars().first()

        if not payment_acc:
            return {
                'success': False,
                'error': '換金先口座が登録されていません。先に「?ショップ」から支払い口座を登録してください。'
            }

        # 口座情報を取得
        account = db.execute(
            select(Account).filter_by(account_id=payment_acc.account_id)
        ).scalars().first()

        if not account:
            return {
                'success': False,
                'error': '登録された口座が見つかりません。'
            }

        # ステータスチェック: activeまたはfrozenのみ有効
        if account.status not in ('active', 'frozen'):
            return {
                'success': False,
                'error': '登録された口座が利用できません（閉鎖済みまたは無効）。'
            }

        branch = db.execute(
            select(Branch).filter_by(branch_id=account.branch_id)
        ).scalars().first()

        if not branch:
            return {
                'success': False,
                'error': '支店情報が見つかりません。'
            }

        # チップ残高を確認・更新
        chip_acc = db.execute(
            select(MinigameChip).filter_by(user_id=user_id).with_for_update()
        ).scalars().first()

        if not chip_acc:
            return {'success': False, 'error': 'チップ残高がありません'}

        # ⚠️ 基本チップのみ換金可能
        available_base = chip_acc.base_balance - chip_acc.locked_base_balance
        if available_base < amt:
            return {
                'success': False,
                'error': f'基本チップが不足しています（必要: {amount}, 利用可能: {int(available_base)}）\n※ボーナスチップは換金できません'
            }

        # 基本チップを減らす
        chip_acc.base_balance -= amt
        # 互換性のため古いフィールドも更新
        chip_acc.balance -= amt
        chip_acc.updated_at = now_jst()

        # 取引履歴を記録
        tx = ChipTransaction(
            user_id=user_id,
            amount=-amt,
            balance_after=chip_acc.base_balance,
            type='redeem',
            chip_type='base',
            description=f'基本チップ{amount}枚を換金'
        )
        db.add(tx)
        db.commit()

        new_base_balance = int(chip_acc.base_balance)

        # 銀行口座に入金（1チップ = 12円で換金）
        redeem_amount = amt * Decimal('12')
        try:
            from apps.shop.shop_service import get_shop_operations_account
            shop_account = get_shop_operations_account()
            deposit_by_account_number(
                account.account_number,
                branch.code,
                redeem_amount,
                'JPY',
                description=f'チップ換金 {amount}枚',
                other_account_info=f"{shop_account['branch_num']}-{shop_account['account_number']}"
            )
        except Exception as e:
            # 入金失敗時はチップをロールバック（別トランザクションなので手動処理）
            db2 = SessionLocal()
            try:
                with db2.begin():
                    chip_acc2 = db2.execute(
                        select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                    ).scalars().first()
                    chip_acc2.base_balance += amt
                    chip_acc2.balance += amt
                    chip_acc2.updated_at = now_jst()

                    tx_refund = ChipTransaction(
                        user_id=user_id,
                        amount=amt,
                        balance_after=chip_acc2.base_balance,
                        type='redeem_failed',
                        chip_type='base',
                        description=f'換金失敗による返金: {amount}枚'
                    )
                    db2.add(tx_refund)
                db2.commit()
            finally:
                db2.close()

            return {
                'success': False,
                'error': f'銀行口座への入金に失敗しました: {str(e)}'
            }

        return {
            'success': True,
            'new_base_balance': new_base_balance,
            'amount_received': int(redeem_amount)
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


def get_chip_history(user_id: str, limit: int = 20) -> List[Dict]:
    """チップ取引履歴を取得"""
    db = SessionLocal()
    try:
        txs = db.execute(
            select(ChipTransaction)
            .filter_by(user_id=user_id)
            .order_by(ChipTransaction.created_at.desc())
            .limit(limit)
        ).scalars().all()

        result = []
        for tx in txs:
            result.append({
                'amount': int(tx.amount),
                'balance_after': int(tx.balance_after),
                'type': tx.type,
                'description': tx.description,
                'created_at': tx.created_at.strftime('%Y/%m/%d %H:%M')
            })

        return result
    finally:
        db.close()
