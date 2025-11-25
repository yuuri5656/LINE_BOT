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


# シングルトンインスタンスをエクスポート
banking_api = BankingAPI()
