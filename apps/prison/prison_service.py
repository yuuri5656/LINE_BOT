"""
懲役システムのビジネスロジック
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, delete
from apps.prison.prison_models import (
    PrisonSentence,
    PrisonRehabilitationFund,
    PrisonRehabilitationDistribution
)
from apps.banking.main_bank_system import (
    SessionLocal,
    Account,
    Customer,
    Transaction,
    TransactionEntry,
)
from apps.banking.bank_service import RESERVE_ACCOUNT_NUMBER, RESERVE_BRANCH_CODE
from apps.utilities.timezone_utils import now_jst

# ============================================
# 給付金専用口座の定義
# ============================================
# 犯罪者更生給付金専用口座（支店: 001, 口座: 4979348）
REHABILITATION_FUND_BRANCH_CODE = '001'
REHABILITATION_FUND_ACCOUNT_NUMBER = '4979348'

# ============================================
# 懲役管理機能
# ============================================

def get_prisoner_status(user_id: str) -> dict:
    """
    ユーザーの懲役ステータスを取得
    
    Returns:
        {
            'is_imprisoned': bool,
            'remaining_days': int or None,
            'end_date': date or None,
            'daily_quota': int or None,
            'completed_today': int or None,
            'last_work_date': date or None
        }
    """
    db = SessionLocal()
    try:
        stmt = select(PrisonSentence).where(PrisonSentence.user_id == user_id)
        sentence = db.execute(stmt).scalars().first()
        
        if not sentence:
            return {
                'is_imprisoned': False,
                'remaining_days': None,
                'end_date': None,
                'daily_quota': None,
                'completed_today': None,
                'last_work_date': None
            }
        
        # 自動釈放チェック
        if sentence.end_date <= date.today():
            release_prisoner(user_id)
            return {
                'is_imprisoned': False,
                'remaining_days': None,
                'end_date': None,
                'daily_quota': None,
                'completed_today': None,
                'last_work_date': None
            }
        
        return {
            'is_imprisoned': True,
            'remaining_days': sentence.remaining_days,
            'end_date': sentence.end_date,
            'daily_quota': sentence.daily_quota,
            'completed_today': sentence.completed_today,
            'last_work_date': sentence.last_work_date
        }
    finally:
        db.close()


def sentence_prisoner(
    user_id: str,
    start_date: date,
    days: int,
    daily_quota: int
) -> dict:
    """
    ユーザーに懲役を設定
    
    Args:
        user_id: 対象ユーザーID
        start_date: 施行日
        days: 懲役日数
        daily_quota: 1日のノルマ（?労働回数）
    
    Returns:
        {
            'success': bool,
            'message': str,
            'sentence_id': int or None
        }
    """
    db = SessionLocal()
    try:
        # 既存の懲役を確認
        existing = db.execute(
            select(PrisonSentence).where(PrisonSentence.user_id == user_id)
        ).scalars().first()
        
        if existing:
            return {
                'success': False,
                'message': f'ユーザー {user_id} は既に懲役中です',
                'sentence_id': None
            }
        
        # ユーザーが存在するか確認
        customer = db.execute(
            select(Customer).where(Customer.user_id == user_id)
        ).scalars().first()
        
        if not customer:
            return {
                'success': False,
                'message': f'ユーザー {user_id} が見つかりません',
                'sentence_id': None
            }
        
        # 釈放日を計算
        end_date = start_date + timedelta(days=days)
        
        # 懲役レコードを作成
        new_sentence = PrisonSentence(
            user_id=user_id,
            customer_id=customer.customer_id,
            start_date=start_date,
            end_date=end_date,
            initial_days=days,
            remaining_days=days,
            daily_quota=daily_quota,
            completed_today=0,
            last_work_date=None
        )
        db.add(new_sentence)
        db.flush()
        sentence_id = new_sentence.sentence_id
        
        # ユーザーの全口座を凍結
        accounts = db.execute(
            select(Account).where(Account.user_id == user_id)
        ).scalars().all()
        
        for account in accounts:
            account.status = 'frozen'
            db.add(account)
        
        db.commit()
        
        return {
            'success': True,
            'message': f'✅ {user_id} に懲役を設定しました\n施行日: {start_date}\n釈放日: {end_date}\n懲役日数: {days}日\n1日のノルマ: {daily_quota}回\n全口座を凍結しました',
            'sentence_id': sentence_id
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}',
            'sentence_id': None
        }
    finally:
        db.close()


def release_prisoner(user_id: str) -> dict:
    """
    ユーザーを釈放（懲役終了）
    
    Returns:
        {
            'success': bool,
            'message': str
        }
    """
    db = SessionLocal()
    try:
        # 懲役レコードを削除
        db.execute(
            delete(PrisonSentence).where(PrisonSentence.user_id == user_id)
        )
        
        # 全口座を復活（status='active'に変更）
        accounts = db.execute(
            select(Account).where(Account.user_id == user_id)
        ).scalars().all()
        
        for account in accounts:
            account.status = 'active'
            db.add(account)
        
        db.commit()
        
        return {
            'success': True,
            'message': f'✅ {user_id} を釈放しました。全口座を復活させました'
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }
    finally:
        db.close()


# ============================================
# 懲役中の?労働処理
# ============================================

def do_prison_work(user_id: str) -> dict:
    """
    懲役中ユーザーの?労働処理
    
    既存の労働システムを流用:
    - 給料: 800～1800円のランダム（既存システムと同じ）
    - 頻度制限: 15分に1回（既存システムと同じ）
    - ノルマカウント +1（懲役システム独自）
    - ノルマ達成時に remaining_days を -1（懲役システム独自）
    - 稼いだ金は給付金専用口座へ振り込み
    
    Returns:
        {
            'success': bool,
            'message': str,
            'quota_completed': bool,
            'remaining_days': int or None,
            'salary': Decimal or None,
            'balance_after': Decimal or None
        }
    """
    import random
    from datetime import timedelta
    db = SessionLocal()
    try:
        from apps.utilities.timezone_utils import now_jst
        
        # 懲役情報を取得
        sentence = db.execute(
            select(PrisonSentence).where(PrisonSentence.user_id == user_id)
        ).scalars().first()
        
        if not sentence:
            return {
                'success': False,
                'message': '懲役情報が見つかりません',
                'quota_completed': False,
                'remaining_days': None,
                'salary': None,
                'balance_after': None
            }
        
        # === 既存システムの頻度制限を流用（15分に1回） ===
        today = date.today()
        if sentence.last_work_date and sentence.last_work_date < today:
            # 日付が変わった場合、タイムスタンプをリセット
            sentence.completed_today = 0
            sentence.last_work_date = today
            # last_work_datetimeもリセット（初回労働を許可）
            sentence.last_work_datetime = None
        elif not sentence.last_work_date:
            sentence.last_work_date = today
            sentence.last_work_datetime = None
        
        # 前回労働からの経過時間をチェック（15分制限）
        if sentence.last_work_datetime:
            now = datetime.now()
            elapsed = now - sentence.last_work_datetime
            if elapsed < timedelta(minutes=15):
                remaining = timedelta(minutes=15) - elapsed
                minutes = int(remaining.total_seconds() / 60)
                seconds = int(remaining.total_seconds() % 60)
                return {
                    'success': False,
                    'message': f'次の労働まで {minutes}分{seconds}秒 待ってください',
                    'quota_completed': False,
                    'remaining_days': sentence.remaining_days,
                    'salary': None,
                    'balance_after': None
                }
        
        # === 既存システムの給料計算を流用（800～1800円のランダム） ===
        salary = Decimal(random.randint(800, 1800))
        
        # ノルマカウント +1
        sentence.completed_today += 1
        quota_completed = sentence.completed_today >= sentence.daily_quota
        
        # 給付金専用口座を取得
        rehabilitation_account = db.execute(
            select(Account).where(
                and_(
                    Account.account_number == REHABILITATION_FUND_ACCOUNT_NUMBER,
                )
            )
        ).scalars().first()
        
        if not rehabilitation_account:
            db.rollback()
            return {
                'success': False,
                'message': '犯罪者更生給付金口座が見つかりません',
                'quota_completed': False,
                'remaining_days': sentence.remaining_days,
                'salary': None,
                'balance_after': None
            }
        
        # 給付金専用口座に振り込み
        rehabilitation_account.balance += salary
        db.add(rehabilitation_account)
        
        # トランザクション記録
        transaction = Transaction(
            to_account_id=rehabilitation_account.account_id,
            type='deposit',
            status='completed',
            amount=salary,
            currency='JPY',
            description=f'懲役中の労働給与: {user_id}',
            executed_at=now_jst()
        )
        db.add(transaction)
        db.flush()
        
        # 最後の労働時刻を更新（15分制限用）
        sentence.last_work_datetime = datetime.now()
        
        # ノルマ達成時に remaining_days を -1
        if quota_completed:
            sentence.remaining_days -= 1
            sentence.completed_today = 0  # リセット
            
            # 釈放日に達したか確認
            if sentence.remaining_days <= 0:
                db.commit()
                release_prisoner(user_id)
                return {
                    'success': True,
                    'message': f'🎉 本日のノルマを達成しました！\n懲役日数: 0日 → **釈放されました**\n全口座が復活しました',
                    'quota_completed': True,
                    'remaining_days': 0,
                    'salary': salary,
                    'balance_after': rehabilitation_account.balance
                }
            
            message = f'✅ 本日のノルマを達成しました！\n残り懲役日数: {sentence.remaining_days}日\n給与: ¥{salary:,} → 給付金口座へ振込'
        else:
            message = f'💼 ?労働を実行しました\nノルマ進捗: {sentence.completed_today}/{sentence.daily_quota}\n給与: ¥{salary:,} → 給付金口座へ振込'
        
        db.add(sentence)
        db.commit()
        
        return {
            'success': True,
            'message': message,
            'quota_completed': quota_completed,
            'remaining_days': sentence.remaining_days,
            'salary': salary,
            'balance_after': rehabilitation_account.balance
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}',
            'quota_completed': False,
            'remaining_days': None,
            'salary': None,
            'balance_after': None
        }
    finally:
        db.close()


# ============================================
# 給付金配布機能
# ============================================

def distribute_rehabilitation_fund() -> dict:
    """
    1日1回実行：犯罪者更生給付金を配布
    
    - 準備預金から全額を回収
    - 懲役中でないすべてのユーザーを取得
    - 金額を平等に分配
    - 各ユーザーの主要口座へ振込
    
    Returns:
        {
            'success': bool,
            'message': str,
            'total_distributed': Decimal,
            'recipient_count': int
        }
    """
    db = SessionLocal()
    try:
        today = date.today()
        
        # 今日既に配布済みか確認
        existing_dist = db.execute(
            select(PrisonRehabilitationDistribution).where(
                PrisonRehabilitationDistribution.distribution_date == today
            )
        ).scalars().first()
        
        if existing_dist:
            return {
                'success': False,
                'message': '本日は既に配布済みです',
                'total_distributed': Decimal('0'),
                'recipient_count': 0
            }
        
        # 給付金専用口座を取得
        rehabilitation_account = db.execute(
            select(Account).where(
                Account.account_number == REHABILITATION_FUND_ACCOUNT_NUMBER
            )
        ).scalars().first()
        
        if not rehabilitation_account or rehabilitation_account.balance <= 0:
            return {
                'success': False,
                'message': '配布可能な資金がありません',
                'total_distributed': Decimal('0'),
                'recipient_count': 0
            }
        
        # 配布対象ユーザー（懲役中でないユーザー）を取得
        imprisoned_users = db.execute(
            select(PrisonSentence.user_id)
        ).scalars().all()
        
        all_customers = db.execute(
            select(Customer)
        ).scalars().all()
        
        recipient_users = [
            c for c in all_customers 
            if c.user_id not in imprisoned_users
        ]
        
        if not recipient_users:
            return {
                'success': False,
                'message': '配布対象ユーザーがいません',
                'total_distributed': Decimal('0'),
                'recipient_count': 0
            }
        
        # 配布額を計算
        total_amount = rehabilitation_account.balance
        recipient_count = len(recipient_users)
        amount_per_recipient = (total_amount / recipient_count).quantize(Decimal('0.01'))
        
        # 各ユーザーに配布
        for customer in recipient_users:
            # ユーザーの最初の口座を取得
            account = db.execute(
                select(Account).where(
                    Account.user_id == customer.user_id
                ).order_by(Account.created_at)
            ).scalars().first()
            
            if not account:
                continue
            
            # 振込
            account.balance += amount_per_recipient
            db.add(account)
            
            # トランザクション記録
            transaction = Transaction(
                from_account_id=rehabilitation_account.account_id,
                to_account_id=account.account_id,
                type='transfer',
                status='completed',
                amount=amount_per_recipient,
                currency='JPY',
                description='犯罪者更生給付金',
                executed_at=now_jst()
            )
            db.add(transaction)
        
        # 給付金専用口座をリセット
        rehabilitation_account.balance = Decimal('0')
        db.add(rehabilitation_account)
        
        # 配布履歴を記録
        distribution = PrisonRehabilitationDistribution(
            distribution_date=today,
            total_amount=total_amount,
            recipient_count=recipient_count,
            amount_per_recipient=amount_per_recipient
        )
        db.add(distribution)
        
        # 給付金口座の更新
        fund_record = db.execute(
            select(PrisonRehabilitationFund).where(
                PrisonRehabilitationFund.account_id == rehabilitation_account.account_id
            )
        ).scalars().first()
        
        if fund_record:
            fund_record.total_collected += total_amount
            fund_record.last_distribution_date = today
            db.add(fund_record)
        
        db.commit()
        
        return {
            'success': True,
            'message': f'✅ 犯罪者更生給付金を配布しました\n配布額: ¥{total_amount:,}\n配布対象: {recipient_count}名\n1人当たり: ¥{amount_per_recipient:,}',
            'total_distributed': total_amount,
            'recipient_count': recipient_count
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}',
            'total_distributed': Decimal('0'),
            'recipient_count': 0
        }
    finally:
        db.close()
