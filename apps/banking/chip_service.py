"""
ミニゲーム用チップ管理サービス
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
import datetime
from typing import Optional, Dict, List

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
                'balance': 0,
                'locked': 0,
                'available': 0
            }

        balance = int(chip_acc.balance)
        locked = int(chip_acc.locked_balance)

        return {
            'balance': balance,
            'locked': locked,
            'available': balance - locked
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
                locked_balance=Decimal('0')
            )
            db.add(chip_acc)
            db.flush()

        return {'success': True, 'message': 'チップアカウントを作成しました'}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def purchase_chips(user_id: str, amount: int, account_number: str, branch_code: str) -> Dict:
    """
    ショップ支払い用口座からチップを購入

    Args:
        user_id: ユーザーID
        amount: チップ枚数（ボーナス込み）
        account_number: 支払い口座番号
        branch_code: 支払い口座の支店コード

    Returns:
        {'success': bool, 'new_balance': int, 'error': str (optional)}
    """
    from apps.banking.bank_service import withdraw_by_account_number, deposit_by_account_number
    from apps.shop.shop_service import get_shop_operations_account

    db = SessionLocal()
    price = Decimal(str(amount))*12  # 1チップ = 12 JPY

    try:
        # 口座から引き落とし
        try:
            withdraw_by_account_number(account_number, branch_code, price, 'JPY')
        except Exception as e:
            return {'success': False, 'error': f'口座からの引き落としに失敗しました: {str(e)}'}

        # ショップ運営口座に売上を入金
        try:
            shop_account = get_shop_operations_account()
            deposit_by_account_number(
                shop_account['account_number'],
                shop_account['branch_num'],
                price,
                'JPY'
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
                chip_acc = MinigameChip(user_id=user_id, balance=Decimal('0'), locked_balance=Decimal('0'))
                db.add(chip_acc)
                db.flush()

            chip_acc.balance += Decimal(str(amount))
            chip_acc.updated_at = datetime.datetime.utcnow()

            # 取引履歴を記録
            tx = ChipTransaction(
                user_id=user_id,
                amount=Decimal(str(amount)),
                balance_after=chip_acc.balance,
                type='purchase',
                description=f'{amount}枚のチップを購入'
            )
            db.add(tx)
            db.flush()

            new_balance = int(chip_acc.balance)

        return {
            'success': True,
            'new_balance': new_balance
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

    Returns:
        {'success': bool, 'new_balance': int, 'error': str (optional)}
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

            available = from_acc.balance - from_acc.locked_balance
            if available < amt:
                raise ValueError(f'利用可能なチップが不足しています（必要: {amount}, 利用可能: {int(available)}）')

            # 受信者のチップアカウント
            to_acc = db.execute(
                select(MinigameChip).filter_by(user_id=to_user_id).with_for_update()
            ).scalars().first()

            if not to_acc:
                to_acc = MinigameChip(user_id=to_user_id, balance=Decimal('0'), locked_balance=Decimal('0'))
                db.add(to_acc)
                db.flush()

            # 転送
            from_acc.balance -= amt
            from_acc.updated_at = datetime.datetime.utcnow()

            to_acc.balance += amt
            to_acc.updated_at = datetime.datetime.utcnow()

            # 履歴記録
            tx_out = ChipTransaction(
                user_id=from_user_id,
                amount=-amt,
                balance_after=from_acc.balance,
                type='transfer_out',
                related_user_id=to_user_id,
                description=f'{to_user_id}へ{amount}枚送信'
            )
            tx_in = ChipTransaction(
                user_id=to_user_id,
                amount=amt,
                balance_after=to_acc.balance,
                type='transfer_in',
                related_user_id=from_user_id,
                description=f'{from_user_id}から{amount}枚受信'
            )
            db.add_all([tx_out, tx_in])
            db.flush()

            new_balance = int(from_acc.balance)

        return {
            'success': True,
            'new_balance': new_balance
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

                    available = chip_acc.balance - chip_acc.locked_balance
                    if available < amt:
                        failed.append({'user_id': user_id, 'error': f'チップ不足（必要:{lock["amount"]}, 利用可能:{int(available)}）'})
                        continue

                    chip_acc.locked_balance += amt
                    chip_acc.updated_at = datetime.datetime.utcnow()

                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=-amt,
                        balance_after=chip_acc.balance,
                        type='game_bet',
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
        distributions: {
            user_id: {
                'locked': int,  # ロックしていた額
                'payout': int   # 賞金額（純粋な獲得分、参加費は含まない）
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
                locked_amt = Decimal(str(dist['locked']))
                payout_amt = Decimal(str(dist['payout']))

                chip_acc = db.execute(
                    select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                ).scalars().first()

                if not chip_acc:
                    continue

                # ロック解除（ベット額を残高から引く）
                chip_acc.balance -= locked_amt
                chip_acc.locked_balance -= locked_amt

                # 賞金付与
                chip_acc.balance += payout_amt
                chip_acc.updated_at = datetime.datetime.utcnow()

                # 履歴記録
                if payout_amt > 0:
                    tx = ChipTransaction(
                        user_id=user_id,
                        amount=payout_amt,
                        balance_after=chip_acc.balance,
                        type='game_win',
                        game_session_id=game_session_id,
                        description=f'ゲーム賞金{int(payout_amt)}枚獲得'
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
    換金率: 1チップ = 12 JPY

    Args:
        user_id: ユーザーID
        amount: 換金するチップ枚数

    Returns:
        {'success': bool, 'new_balance': int, 'amount_received': int, 'error': str (optional)}
    """
    from apps.banking.bank_service import deposit_by_account_number
    from apps.banking.api import banking_api

    db = SessionLocal()
    amt = Decimal(str(amount))
    new_balance = 0

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

        available = chip_acc.balance - chip_acc.locked_balance
        if available < amt:
            return {
                'success': False,
                'error': f'利用可能なチップが不足しています（必要: {amount}, 利用可能: {int(available)}）'
            }

        # チップを減らす
        chip_acc.balance -= amt
        chip_acc.updated_at = datetime.datetime.utcnow()

        # 取引履歴を記録
        tx = ChipTransaction(
            user_id=user_id,
            amount=-amt,
            balance_after=chip_acc.balance,
            type='redeem',
            description=f'{amount}枚のチップを換金'
        )
        db.add(tx)
        db.commit()

        new_balance = int(chip_acc.balance)

        # 銀行口座に入金（1チップ = 12円で換金）
        redeem_amount = amt * Decimal('12')
        try:
            deposit_by_account_number(
                account.account_number,
                branch.code,
                redeem_amount,
                'JPY'
            )
        except Exception as e:
            # 入金失敗時はチップをロールバック（別トランザクションなので手動処理）
            db2 = SessionLocal()
            try:
                with db2.begin():
                    chip_acc2 = db2.execute(
                        select(MinigameChip).filter_by(user_id=user_id).with_for_update()
                    ).scalars().first()
                    chip_acc2.balance += amt
                    chip_acc2.updated_at = datetime.datetime.utcnow()

                    tx_refund = ChipTransaction(
                        user_id=user_id,
                        amount=amt,
                        balance_after=chip_acc2.balance,
                        type='redeem_failed',
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
            'new_balance': new_balance,
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
