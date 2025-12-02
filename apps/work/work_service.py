"""
労働システムのビジネスロジック
"""
from typing import Optional, Dict
from decimal import Decimal
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from apps.banking.main_bank_system import get_db
from apps.banking.api import banking_api


def get_salary_account_info(user_id: str) -> Optional[Dict]:
    """
    ユーザーの給与振込口座情報を取得

    Returns:
        給与振込口座情報辞書、未登録の場合はNone
    """
    db = next(get_db())
    try:
        query = text("""
            SELECT wsa.salary_account_id, wsa.user_id, wsa.account_id,
                   wsa.registered_at, wsa.last_work_at, wsa.is_active,
                   a.account_number, b.code as branch_code, b.name as branch_name,
                   c.full_name, a.balance, a.currency
            FROM work_salary_accounts wsa
            JOIN accounts a ON wsa.account_id = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
            LEFT JOIN branches b ON a.branch_id = b.branch_id
            WHERE wsa.user_id = :user_id AND wsa.is_active = TRUE
            LIMIT 1
        """)
        result = db.execute(query, {"user_id": user_id}).fetchone()

        if result:
            return {
                'salary_account_id': result[0],
                'user_id': result[1],
                'account_id': result[2],
                'registered_at': result[3],
                'last_work_at': result[4],
                'is_active': result[5],
                'account_number': result[6],
                'branch_code': result[7],
                'branch_name': result[8],
                'full_name': result[9],
                'balance': result[10],
                'currency': result[11]
            }
        return None
    finally:
        db.close()


def register_salary_account_by_id(user_id: str, account_id: int) -> Dict:
    """
    account_idで給与振込口座を登録

    Returns:
        {'success': True/False, 'message': str}
    """
    db = next(get_db())
    try:
        # 既存の登録があるか確認
        existing = get_salary_account_info(user_id)
        if existing:
            return {'success': False, 'message': '既に給与振込口座が登録されています'}

        # 口座が存在するか確認
        account_query = text("""
            SELECT a.account_id, c.full_name, b.code as branch_code, a.account_number
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            LEFT JOIN branches b ON a.branch_id = b.branch_id
            WHERE a.account_id = :account_id AND a.user_id = :user_id AND a.status = 'active'
        """)
        account = db.execute(account_query, {"account_id": account_id, "user_id": user_id}).fetchone()

        if not account:
            return {'success': False, 'message': '指定された口座が見つかりません'}

        # 給与振込口座を登録
        insert_query = text("""
            INSERT INTO work_salary_accounts (user_id, account_id, registered_at, is_active)
            VALUES (:user_id, :account_id, CURRENT_TIMESTAMP, TRUE)
            RETURNING salary_account_id
        """)
        result = db.execute(insert_query, {"user_id": user_id, "account_id": account_id}).fetchone()
        db.commit()

        return {
            'success': True,
            'message': '給与振込口座を登録しました',
            'account_number': account[3],
            'branch_code': account[2]
        }
    except Exception as e:
        db.rollback()
        print(f"[Work Service] Error registering salary account: {e}")
        return {'success': False, 'message': f'登録中にエラーが発生しました: {str(e)}'}
    finally:
        db.close()


def can_work(user_id: str) -> Dict:
    """
    労働可能かどうかをチェック（15分に1回制限）

    Returns:
        {'can_work': bool, 'message': str, 'next_available_at': datetime}
    """
    salary_info = get_salary_account_info(user_id)

    if not salary_info:
        return {'can_work': False, 'message': '給与振込口座が登録されていません', 'next_available_at': None}

    last_work_at = salary_info.get('last_work_at')

    if not last_work_at:
        # 初回労働
        return {'can_work': True, 'message': 'OK', 'next_available_at': None}

    # 15分経過したかチェック
    now = datetime.now()
    next_available = last_work_at + timedelta(minutes=15)

    if now >= next_available:
        return {'can_work': True, 'message': 'OK', 'next_available_at': None}
    else:
        remaining = next_available - now
        minutes = int(remaining.total_seconds() / 60)
        seconds = int(remaining.total_seconds() % 60)
        return {
            'can_work': False,
            'message': f'次の労働まで {minutes}分{seconds}秒 待ってください',
            'next_available_at': next_available
        }


def do_work(user_id: str) -> Dict:
    """
    労働を実行し、給与を口座に振り込む

    Returns:
        {'success': bool, 'salary': Decimal, 'message': str, 'balance_after': Decimal}
    """
    # 労働可能かチェック
    can_work_result = can_work(user_id)
    if not can_work_result['can_work']:
        return {
            'success': False,
            'salary': Decimal('0'),
            'message': can_work_result['message'],
            'balance_after': Decimal('0')
        }

    # 給与額を決定（800円～1800円のランダム）
    salary = Decimal(random.randint(800, 1800))

    # 給与振込口座情報を取得
    salary_info = get_salary_account_info(user_id)
    if not salary_info:
        return {
            'success': False,
            'salary': Decimal('0'),
            'message': '給与振込口座が見つかりません',
            'balance_after': Decimal('0')
        }

    account_id = salary_info['account_id']
    account_number = salary_info['account_number']
    branch_code = salary_info['branch_code']

    db = next(get_db())
    try:
        # 口座に入金
        success = banking_api.deposit_by_account(account_number, branch_code, salary, 'JPY')

        if not success:
            return {
                'success': False,
                'salary': salary,
                'message': '給与の振り込みに失敗しました',
                'balance_after': Decimal('0')
            }

        # 最終労働時刻を更新
        update_query = text("""
            UPDATE work_salary_accounts
            SET last_work_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """)
        db.execute(update_query, {"user_id": user_id})

        # 労働履歴を記録
        history_query = text("""
            INSERT INTO work_history (user_id, salary_amount, account_id, worked_at, description)
            VALUES (:user_id, :salary, :account_id, CURRENT_TIMESTAMP, '労働報酬')
        """)
        db.execute(history_query, {"user_id": user_id, "salary": salary, "account_id": account_id})
        db.commit()

        # 入金後の残高を取得（口座情報を再取得）
        balance_query = text("""
            SELECT balance FROM accounts
            WHERE account_number = :account_number AND branch_id = (
                SELECT branch_id FROM branches WHERE code = :branch_code
            )
        """)
        balance_result = db.execute(balance_query, {"account_number": account_number, "branch_code": branch_code}).fetchone()
        balance_after = balance_result[0] if balance_result else Decimal('0')

        return {
            'success': True,
            'salary': salary,
            'message': f'労働完了！給与 ¥{salary:,} を振り込みました',
            'balance_after': balance_after or Decimal('0')
        }
    except Exception as e:
        db.rollback()
        print(f"[Work Service] Error doing work: {e}")
        return {
            'success': False,
            'salary': salary,
            'message': f'エラーが発生しました: {str(e)}',
            'balance_after': Decimal('0')
        }
    finally:
        db.close()


def get_work_history(user_id: str, limit: int = 20) -> list:
    """
    労働履歴を取得

    Returns:
        労働履歴のリスト
    """
    db = next(get_db())
    try:
        query = text("""
            SELECT wh.work_id, wh.salary_amount, wh.worked_at, wh.description,
                   a.account_number, b.code as branch_code, b.name as branch_name
            FROM work_history wh
            JOIN accounts a ON wh.account_id = a.account_id
            LEFT JOIN branches b ON a.branch_id = b.branch_id
            WHERE wh.user_id = :user_id
            ORDER BY wh.worked_at DESC
            LIMIT :limit
        """)
        results = db.execute(query, {"user_id": user_id, "limit": limit}).fetchall()

        history = []
        for row in results:
            history.append({
                'work_id': row[0],
                'salary_amount': row[1],
                'worked_at': row[2],
                'description': row[3],
                'account_number': row[4],
                'branch_code': row[5],
                'branch_name': row[6]
            })
        return history
    finally:
        db.close()
