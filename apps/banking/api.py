"""
銀行機能APIファサード
外部からの銀行機能アクセスはこのモジュールを経由すること
bank_service.pyへの直接アクセスは禁止
"""
from typing import Optional, Dict, List, Any
from decimal import Decimal


# 内部モジュールのインポート（外部からは隠蔽）
def _get_bank_service():
    """遅延インポートでbank_serviceを取得（循環import回避）"""
    from apps.banking import bank_service
    return bank_service


class BankingAPI:
    """銀行機能の統一インターフェース"""

    # --- 口座管理 ---

    @staticmethod
    def create_account(event, account_info: dict, sessions: dict, operator_id: Optional[str] = None) -> dict:
        """
        口座を開設する

        Args:
            event: LINEイベントオブジェクト
            account_info: 口座情報（user_id, full_name, birth_date, pin_code等）
            sessions: セッション辞書
            operator_id: 操作者ID（オプション）

        Returns:
            作成された口座の情報辞書
        """
        service = _get_bank_service()
        return service.create_account_optimized(event, account_info, sessions, operator_id)

    @staticmethod
    def reply_account_creation(event, account_info: dict, account_data: dict):
        """
        口座開設完了メッセージを送信

        Args:
            event: LINEイベントオブジェクト
            account_info: 元の口座情報
            account_data: 作成された口座データ
        """
        service = _get_bank_service()
        service.reply_account_creation(event, account_info, account_data)

    @staticmethod
    def get_account_by_user(user_id: str) -> Optional[dict]:
        """
        ユーザーIDから口座情報を取得

        Args:
            user_id: LINE user ID

        Returns:
            口座情報辞書、見つからない場合はNone
        """
        service = _get_bank_service()
        return service.get_account_info_by_user(user_id)

    @staticmethod
    def get_accounts_by_user(user_id: str) -> List[dict]:
        """
        ユーザーIDに紐づく全口座情報を取得

        Args:
            user_id: LINE user ID

        Returns:
            口座情報辞書のリスト
        """
        service = _get_bank_service()
        return service.get_accounts_by_user(user_id)

    @staticmethod
    def get_active_account(user_id: str):
        """
        アクティブな口座を取得

        Args:
            user_id: LINE user ID

        Returns:
            Accountオブジェクト、見つからない場合はNone
        """
        service = _get_bank_service()
        return service.get_active_account_by_user(user_id)

    # --- 取引 ---

    @staticmethod
    def transfer(from_account_number: str, to_account_number: str,
                 amount: Any, currency: str = 'JPY'):
        """
        口座間送金

        Args:
            from_account_number: 送金元口座番号
            to_account_number: 送金先口座番号
            amount: 金額
            currency: 通貨コード

        Returns:
            Transactionオブジェクト
        """
        service = _get_bank_service()
        return service.transfer_funds(from_account_number, to_account_number, amount, currency)

    @staticmethod
    def withdraw_by_account(account_number: str, branch_code: str,
                            amount: Any, currency: str = 'JPY') -> bool:
        """
        口座番号・支店コードで引き落とし

        Args:
            account_number: 口座番号
            branch_code: 支店コード
            amount: 引き落とし額
            currency: 通貨コード

        Returns:
            成功時True
        """
        service = _get_bank_service()
        return service.withdraw_by_account_number(account_number, branch_code, amount, currency)

    @staticmethod
    def deposit_by_account(account_number: str, branch_code: str,
                          amount: Any, currency: str = 'JPY') -> bool:
        """
        口座番号・支店コードで入金

        Args:
            account_number: 口座番号
            branch_code: 支店コード
            amount: 入金額
            currency: 通貨コード

        Returns:
            成功時True
        """
        service = _get_bank_service()
        return service.deposit_by_account_number(account_number, branch_code, amount, currency)

    # --- 取引履歴 ---

    @staticmethod
    def get_transactions(account_number: str, branch_code: str, limit: int = 20) -> List[dict]:
        """
        取引履歴を取得（口座番号・支店コードベース）

        Args:
            account_number: 口座番号
            branch_code: 支店コード
            limit: 取得件数上限

        Returns:
            取引履歴辞書のリスト
        """
        service = _get_bank_service()
        return service.get_account_transactions_by_account(account_number, branch_code, limit)

    # --- ミニゲーム口座 ---

    @staticmethod
    def register_minigame_account(user_id: str, full_name: str,
                                  branch_code: str, account_number: str,
                                  pin_code: str) -> dict:
        """
        ミニゲーム用口座を登録

        Args:
            user_id: LINE user ID
            full_name: フルネーム（半角カナ）
            branch_code: 支店コード
            account_number: 口座番号
            pin_code: 暗証番号

        Returns:
            {'success': bool, 'message': str, ...}
        """
        service = _get_bank_service()
        return service.register_minigame_account(user_id, full_name, branch_code,
                                                account_number, pin_code)

    @staticmethod
    def get_minigame_account(user_id: str):
        """
        ミニゲーム用口座を取得

        Args:
            user_id: LINE user ID

        Returns:
            Accountオブジェクト、未登録の場合はNone
        """
        service = _get_bank_service()
        return service.get_minigame_account(user_id)

    @staticmethod
    def get_minigame_account_info(user_id: str) -> Optional[dict]:
        """
        ミニゲーム用口座情報を取得

        Args:
            user_id: LINE user ID

        Returns:
            口座情報辞書、未登録の場合はNone
        """
        service = _get_bank_service()
        return service.get_minigame_account_info(user_id)

    @staticmethod
    def unregister_minigame_account(user_id: str) -> dict:
        """
        ミニゲーム用口座登録を解除

        Args:
            user_id: LINE user ID

        Returns:
            {'success': bool, 'message': str}
        """
        service = _get_bank_service()
        return service.unregister_minigame_account(user_id)

    # --- 認証 ---

    @staticmethod
    def authenticate_customer(full_name: str, pin_code: str,
                             branch_code: Optional[str] = None,
                             account_number: Optional[str] = None) -> bool:
        """
        顧客認証

        Args:
            full_name: フルネーム
            pin_code: 暗証番号
            branch_code: 支店コード（オプション）
            account_number: 口座番号（オプション）

        Returns:
            認証成功時True
        """
        service = _get_bank_service()
        return service.authenticate_customer(full_name, pin_code, branch_code, account_number)

    # --- 定数 ---

    @staticmethod
    def get_minigame_fee_account() -> dict:
        """ミニゲーム手数料受取口座情報を取得"""
        service = _get_bank_service()
        return service.MINIGAME_FEE_ACCOUNT

    # --- バッチ処理（ミニゲーム用最適化） ---

    @staticmethod
    def batch_withdraw_minigame(user_ids: list, amount: int) -> dict:
        """
        複数ユーザーのミニゲーム口座から一括引き落とし

        Args:
            user_ids: ユーザーIDのリスト
            amount: 各ユーザーから引き落とす額

        Returns:
            {
                'success': bool,
                'completed': [list of user_ids],
                'failed': [list of user_ids],
                'total_amount': Decimal,
                'error': str (optional)
            }
        """
        service = _get_bank_service()
        withdrawals = []
        user_account_map = {}  # user_id -> account_number のマッピング

        for user_id in user_ids:
            minigame_info = service.get_minigame_account_info(user_id)
            if not minigame_info:
                # ミニゲーム口座が未登録のユーザーはスキップ
                continue

            account_number = minigame_info.get('account_number')
            branch_code = minigame_info.get('branch_code')

            if account_number and branch_code:
                withdrawals.append({
                    'account_number': account_number,
                    'branch_code': branch_code,
                    'amount': amount
                })
                user_account_map[account_number] = user_id

        if not withdrawals:
            return {
                'success': False,
                'completed': [],
                'failed': user_ids,
                'total_amount': Decimal('0'),
                'error': 'No valid minigame accounts found'
            }

        result = service.batch_withdraw(withdrawals)

        # account_numberをuser_idに変換
        completed_users = [user_account_map.get(acc_num) for acc_num in result.get('completed', [])]
        failed_users = [uid for uid in user_ids if uid not in completed_users]

        return {
            'success': result.get('success', False),
            'completed': completed_users,
            'failed': failed_users,
            'total_amount': result.get('total_amount', Decimal('0')),
            'error': result.get('failed', [{}])[0].get('error') if result.get('failed') else None
        }

    @staticmethod
    def batch_deposit_minigame(payouts: dict) -> dict:
        """
        複数ユーザーのミニゲーム口座へ一括入金

        Args:
            payouts: {user_id: amount, ...}

        Returns:
            {
                'success': bool,
                'completed': [list of user_ids],
                'failed': [list of user_ids],
                'total_amount': Decimal,
                'error': str (optional)
            }
        """
        service = _get_bank_service()
        deposits = []
        user_account_map = {}  # user_id -> account_number のマッピング

        for user_id, amount in payouts.items():
            if amount <= 0:
                continue

            minigame_info = service.get_minigame_account_info(user_id)
            if not minigame_info:
                continue

            account_number = minigame_info.get('account_number')
            branch_code = minigame_info.get('branch_code')

            if account_number and branch_code:
                deposits.append({
                    'account_number': account_number,
                    'branch_code': branch_code,
                    'amount': amount
                })
                user_account_map[account_number] = user_id

        if not deposits:
            return {
                'success': False,
                'completed': [],
                'failed': list(payouts.keys()),
                'total_amount': Decimal('0'),
                'error': 'No valid minigame accounts found'
            }

        result = service.batch_deposit(deposits)

        # account_numberをuser_idに変換
        completed_users = [user_account_map.get(acc_num) for acc_num in result.get('completed', [])]
        failed_users = [uid for uid in payouts.keys() if uid not in completed_users]

        return {
            'success': result.get('success', False),
            'completed': completed_users,
            'failed': failed_users,
            'total_amount': result.get('total_amount', Decimal('0')),
            'error': result.get('failed', [{}])[0].get('error') if result.get('failed') else None
        }


# シングルトンインスタンスをエクスポート
banking_api = BankingAPI()
