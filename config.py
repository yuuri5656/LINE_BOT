import os

from decimal import Decimal

def _get_env_or_raise(key: str) -> str:
	val = os.environ.get(key)
	if not val:
		raise RuntimeError(f"Required environment variable '{key}' is not set")
	return val

LINE_CHANNEL_SECRET = _get_env_or_raise('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = _get_env_or_raise('LINE_CHANNEL_ACCESS_TOKEN')
DATABASE_URL = _get_env_or_raise('DATABASE_URL')
# 任意: 管理者/作成者のLINE userId。設定されていれば口座作成完了通知を個別送信する。
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID')
# 画像アップロードAPI設定（チャート画像用）
# Imgur: https://imgur.com/account/settings/apps でClient IDを取得
IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
# ImgBB（代替）: https://api.imgbb.com/ でAPI Keyを取得
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')

# =========================================
# Tax / Loans / Collections (Option A config)
# =========================================

# 税金の振込先（固定）
TAX_DEST_BRANCH_CODE = '001'
TAX_DEST_ACCOUNT_NUMBER = '1111111'

# 税の基本設定
TAX_NON_TAXABLE_THRESHOLD = Decimal('10000')
TAX_ROUND_UNIT = Decimal('1000')
TAX_PENALTY_WEEKLY_RATE = Decimal('0.15')
TAX_SEIZURE_DAYS = 14

# 所得税率表（週次所得に適用）
TAX_BRACKETS = [
	{'min': Decimal('10000'), 'max': Decimal('99000'), 'rate': Decimal('0.05'), 'deduction': Decimal('0')},
	{'min': Decimal('100000'), 'max': Decimal('499000'), 'rate': Decimal('0.30'), 'deduction': Decimal('30000')},
	{'min': Decimal('500000'), 'max': Decimal('1499000'), 'rate': Decimal('0.40'), 'deduction': Decimal('100000')},
	{'min': Decimal('1500000'), 'max': Decimal('3499000'), 'rate': Decimal('0.50'), 'deduction': Decimal('700000')},
	{'min': Decimal('3500000'), 'max': None, 'rate': Decimal('0.60'), 'deduction': Decimal('1300000')},
]

# ギャンブル所得（換金時）
GAMBLE_SPECIAL_DEDUCTION = Decimal('100000')

# ローン設定
LOAN_LENDER_BRANCH_CODE = '001'
LOAN_LENDER_ACCOUNT_NUMBER = '7777777'  # 準備預金口座を貸付元/回収先として流用
LOAN_MIN_PRINCIPAL = Decimal('10000')
LOAN_MAX_MULTIPLIER = Decimal('5')
# 利率（週）
# 仕様: (principal / prev_income) * LOAN_INTEREST_FACTOR をベースにし、上限を適用。
# 借入上限が「前週所得×5」なので、factor=0.016 にすると最大で約8%/週（5×0.016=0.08）になります。
LOAN_INTEREST_FACTOR = Decimal('0.016')
LOAN_INTEREST_RATE_CAP = Decimal('0.08')
LOAN_LATE_WEEKLY_RATE = Decimal('0.20')
