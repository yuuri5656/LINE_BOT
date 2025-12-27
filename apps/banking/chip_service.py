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


def _merge_bonus_into_base(chip_acc: MinigameChip) -> None:
    """ボーナスチップ廃止: 既存データのbonus系をbase系へ統合して0に寄せる。"""
    bonus = getattr(chip_acc, 'bonus_balance', None) or Decimal('0')
    locked_bonus = getattr(chip_acc, 'locked_bonus_balance', None) or Decimal('0')

    if bonus != 0:
        chip_acc.base_balance += bonus
        chip_acc.bonus_balance = Decimal('0')

    if locked_bonus != 0:
        chip_acc.locked_base_balance += locked_bonus
        chip_acc.locked_bonus_balance = Decimal('0')

    # 互換性フィールドを同期
    chip_acc.balance = chip_acc.base_balance
    chip_acc.locked_balance = chip_acc.locked_base_balance


def get_chip_balance(user_id: str) -> Dict:
    """
    ユーザーのチップ残高を取得

    Returns:
        ※ボーナスチップ廃止: チップは1種類のみ。
        互換性のためキーは残すが、bonus系は常に0。
        {
            'base_balance': int,
            'bonus_balance': int,
            'locked_base_balance': int,
            'locked_bonus_balance': int,
            'available_base': int,
            'available_bonus': int,
            'balance': int,
            'locked': int,
            'available': int
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
                'available_bonus': 0,
                'balance': 0,
                'locked': 0,
                'available': 0
            }

        base_balance = int(chip_acc.base_balance)
        bonus_balance = int(getattr(chip_acc, 'bonus_balance', 0) or 0)
        locked_base = int(chip_acc.locked_base_balance)
        locked_bonus = int(getattr(chip_acc, 'locked_bonus_balance', 0) or 0)

        total_balance = base_balance + bonus_balance
        total_locked = locked_base + locked_bonus
        available_total = total_balance - total_locked

        return {
            'base_balance': total_balance,
            'bonus_balance': 0,
            'locked_base_balance': total_locked,
            'locked_bonus_balance': 0,
            'available_base': available_total,
            'available_bonus': 0,
            'balance': total_balance,
            'locked': total_locked,
            'available': available_total
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
        base_amount: 付与チップ枚数（ボーナス廃止により単一）
        bonus_amount: 互換性のため残す（常にbaseに合算）
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

            _merge_bonus_into_base(chip_acc)

            total_amount = int(base_amount) + int(bonus_amount)
            total_amt = Decimal(str(total_amount))

            chip_acc.base_balance += total_amt
            chip_acc.bonus_balance = Decimal('0')

            # 互換性のため古いフィールドも同時に更新
            chip_acc.balance += total_amt
            chip_acc.updated_at = now_jst()

            # 取引履歴を記録（チップは1種類）
            if total_amount > 0:
                tx = ChipTransaction(
                    user_id=user_id,
                    amount=total_amt,
                    balance_after=chip_acc.base_balance,
                    type='purchase',
                    chip_type='base',
                    description=f'チップ{total_amount}枚を購入'
                )
                db.add(tx)
            
            db.flush()

            new_base_balance = int(chip_acc.base_balance)
            new_bonus_balance = 0

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
    ボーナスチップ廃止: チップは全て転送可能

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

            _merge_bonus_into_base(from_acc)

            available = from_acc.base_balance - from_acc.locked_base_balance
            if available < amt:
                raise ValueError(f'利用可能なチップが不足しています（必要: {amount}, 利用可能: {int(available)}）')

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

            _merge_bonus_into_base(to_acc)

            # 転送（チップは1種類）
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
                description=f'{to_user_id}へチップ{amount}枚送信'
            )
            tx_in = ChipTransaction(
                user_id=to_user_id,
                amount=amt,
                balance_after=to_acc.base_balance,
                type='transfer_in',
                chip_type='base',
                related_user_id=from_user_id,
                description=f'{from_user_id}からチップ{amount}枚受信'
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
    ボーナスチップ廃止: ロック対象は単一チップのみ

    Args:
        locks: [{'user_id': str, 'amount': int, 'game_session_id': str}, ...]
    
    Returns:
        {
            'success': bool,
            'completed': [{'user_id': str, 'locked_base': int, 'locked_bonus': int}, ...],
            'failed': [...]
        }
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

                    _merge_bonus_into_base(chip_acc)

                    available = chip_acc.base_balance - chip_acc.locked_base_balance
                    if available < amt:
                        failed.append({'user_id': user_id, 'error': f'チップ不足（必要:{lock["amount"]}, 利用可能:{int(available)}）'})
                        continue

                    locked_base = amt
                    locked_bonus = Decimal('0')
                    chip_acc.locked_base_balance += locked_base
                    locked_type = 'base'

                    # 互換性フィールドも更新
                    chip_acc.locked_balance += amt

                    chip_acc.updated_at = now_jst()

                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=-amt,
                        balance_after=chip_acc.base_balance,
                        type='game_bet',
                        chip_type=locked_type,
                        game_session_id=game_session_id,
                        description=f'ゲーム参加費{lock["amount"]}枚'
                    )
                    db.add(tx)

                    completed.append({
                        'user_id': user_id,
                        'locked_base': int(locked_base),
                        'locked_bonus': int(locked_bonus)
                    })

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
                'locked_base': int,   # ロックしたチップ
                'locked_bonus': int,  # 互換性（常に0）
                'payout': int         # 総払戻額（ベット返却を含む）
            },
            ...
        }
        
        フォーマット2（旧・互換性）:
        {
            user_id: {
                'locked': int,   # ロック総額
                'payout': int    # 総払戻額（ベット返却を含む）
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
                
                payout_total_amt = Decimal(str(dist['payout']))

                chip_acc = db.execute(
                    select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                ).scalars().first()

                if not chip_acc:
                    continue

                _merge_bonus_into_base(chip_acc)

                locked_total = locked_base_amt + locked_bonus_amt

                # ロック解除（ロック残高のみ減らす）
                chip_acc.locked_base_balance -= locked_total
                chip_acc.locked_balance -= locked_total

                # 精算差分 = 総払戻 - ベット（ロック額）
                delta = payout_total_amt - locked_total
                chip_acc.base_balance += delta
                chip_acc.balance += delta
                chip_acc.updated_at = now_jst()

                # 履歴記録（増加のみ）
                if delta > 0:
                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=delta,
                        balance_after=chip_acc.base_balance,
                        type='game_win',
                        chip_type='base',
                        game_session_id=game_session_id,
                        description=f'ゲーム獲得{int(delta)}枚'
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
    ボーナスチップ廃止: チップは全て換金可能
    換金率: 1チップ = 12 JPY

    Args:
        user_id: ユーザーID
        amount: 換金するチップ枚数（基本チップのみ）

    Returns:
        {'success': bool, 'new_base_balance': int, 'amount_received': int, 'error': str (optional)}
    """
    from apps.banking.bank_service import deposit_by_account_number_return_tx_id
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

        _merge_bonus_into_base(chip_acc)

        available = chip_acc.base_balance - chip_acc.locked_base_balance
        if available < amt:
            return {
                'success': False,
                'error': f'チップが不足しています（必要: {amount}, 利用可能: {int(available)}）'
            }

        # チップを減らす
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
            description=f'チップ{amount}枚を換金'
        )
        db.add(tx)
        db.commit()

        new_base_balance = int(chip_acc.base_balance)

        # 銀行口座に入金（1チップ = 12円で換金）
        redeem_amount = amt * Decimal('12')
        try:
            from apps.shop.shop_service import get_shop_operations_account
            shop_account = get_shop_operations_account()
            tx_id = deposit_by_account_number_return_tx_id(
                account.account_number,
                branch.code,
                redeem_amount,
                'JPY',
                description=f'チップ換金 {amount}枚',
                other_account_info=f"{shop_account['branch_num']}-{shop_account['account_number']}"
            )

            # 税: ギャンブル所得（換金時）を記録
            try:
                from apps.tax.tax_service import record_gamble_cashout_income
                record_gamble_cashout_income(
                    user_id=user_id,
                    bank_transaction_id=int(tx_id),
                    cashout_amount=redeem_amount,
                )
            except Exception as tax_err:
                print(f"[ChipService] tax income record failed user={user_id} err={tax_err}")
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
