# サブシステム: Prison（拘置所）

## 概要
`apps/prison` は拘置所システムに関する業務ロジック（収容者管理、作業スケジューラ、リハビリ計画）を扱います。

## 主要責務
- 受刑者の状態管理とステータス更新
- 作業スケジュールと割当
- リハビリテーション計画の管理

## 主要ファイル
- `apps/prison/prison_service.py` — ドメインロジック
- `apps/prison/rehabilitation_scheduler.py` — スケジューラロジック
- `apps/prison/prison_models.py` — モデル定義（データ構造）

## データフロー（作業割当の例）
1. 管理者コマンドでスケジュールを作成
2. `rehabilitation_scheduler` で候補者を選定し割当
3. 結果をDBに記録し、該当ユーザーへ通知

## 注意点
- 個人データの取り扱いと適切なアクセス制御
- スケジューリングの競合解決

## 参照
- 関連コード: [apps/prison](../../apps/prison)

## 主要関数 / クラス
- `run_daily_distribution()`
- `start_rehabilitation_distribution_scheduler()`
- `stop_rehabilitation_distribution_scheduler()`
- `is_admin(user_id: str) -> bool`
- `handle_admin_user_accounts(event, user_id: str, target_user_id: str)`
- `handle_admin_account_number(event, user_id: str, account_number: str)`
- `handle_admin_sentence(event, user_id: str, target_user_id: str, start_date_str: str, days: int, quota: int)`
- `handle_admin_freeze_account(event, user_id: str, account_number: str)`
- `handle_admin_release(event, user_id: str, target_user_id: str)`
- `get_prison_work_result_flex(result: dict) -> FlexSendMessage`
- `get_prison_status_flex(prisoner_status: dict, user_id: str) -> FlexSendMessage`
- `get_prisoner_status(user_id: str) -> dict`
- `sentence_prisoner(...)`
- `release_prisoner(user_id: str) -> dict`
- `do_prison_work(user_id: str) -> dict`
- `distribute_rehabilitation_fund() -> dict`

