# 税・借金（ローン）・回収（督促/延滞/ブラックリスト/差押え） 実装ドキュメント

このドキュメントは、税（週次課税＋納付）および借金（ローン）と、両者に共通する回収（督促/延滞/ブラックリスト/差押え）を **DB設計からアプリ処理フローまで** 一気通貫で説明します。

対象コード/SQL（主要）：
- DB: `migrations/create_tax_and_collections_system.sql`, `migrations/create_loan_system.sql`
- 権限: `migrations/grant_tax_loan_collections_privileges.sql`
- 税: `apps/tax/tax_service.py`, `apps/tax/models.py`, `apps/tax/tax_scheduler.py`, `apps/tax/ui.py`, `apps/tax/commands.py`
- ローン: `apps/loans/loan_service.py`, `apps/loans/models.py`, `apps/loans/ui.py`, `apps/loans/commands.py`
- 回収: `apps/collections/collections_service.py`, `apps/collections/models.py`
- 入口: `main.py`, `apps/auto_reply.py`

---

## 1. 全体アーキテクチャ概要

### 1-1. 役割分担

- **Tax（税）**
  - 週次で「所得イベント（台帳）」を集計し、税額を確定（`tax_assessments`）
  - 税額がある場合、回収ケース（`collections_cases`）を作成
  - 設定済みの納税口座があれば **自動納付**（銀行振込）を試行
  - ユーザーは `?税`（Flex UI）または `?納税`（テキスト）で確認/設定/納付

- **Loans（借金/ローン）**
  - 借入審査は「前週所得」「ブラックリスト」を参照
  - 借入成立で準備口座からユーザー口座へ入金（銀行振込）
  - 日次で利息を積み上げ（延滞中は遅延損害金）
  - 日次で自動引落（失敗が続くと回収側へ連携）
  - ユーザーは `?借金`（Flex UI）または `?借入`/`?返済`（テキスト）で操作

- **Collections（回収/信用情報）**
  - 税/ローン共通の「回収ケース」を管理（督促・延滞・差押え）
  - `credit_profile` にブラックリスト状態を持つ
  - 日次で回収判定を進め、延滞税/利息の増分記録、ブラック化、差押え（銀行残高回収）を実行
  - 個別チャットでは **全発言に対し督促文をPush** する（返信枠を消費しない）

### 1-2. 定期実行（スケジューラ）

`apps/tax/tax_scheduler.py` の APScheduler が `main.py` 起動時に開始されます。

- 週次（日曜 15:00 JST）: 課税確定 + 自動納付
- 日次（10:00 JST）: ローン利息 + ローン自動引落
- 日次（10:10 JST）: 回収（延滞/ブラック化/差押え）

> 回収はローン自動引落の後（10:10）に走るため、「引落失敗 → 延滞判定」の順序が安定します。

---

## 2. データベース設計

### 2-1. 税（Tax）テーブル

SQL: `migrations/create_tax_and_collections_system.sql`

#### `tax_profiles`（納税口座設定）
- `user_id`（PK）
- `tax_account_id`（FK -> `accounts.account_id`, NULL可, SET NULL）
- `created_at`, `updated_at`

用途:
- ユーザーが「納税に使う口座」を設定する（自動納付/手動納付に利用）

#### `tax_periods`（週次期間）
- `period_id`（PK）
- `start_at`, `end_at`（UNIQUE）

用途:
- 「前週の集計期間」を半開区間 `[start_at, end_at)` として一意管理

#### `tax_income_events`（所得イベント台帳）
- `event_id`（PK）
- `user_id`, `occurred_at`
- `category`（例: work_salary / stock_dividend / stock_sale_profit / gamble_cashout 等）
- `amount`（総額）
- `taxable_amount`（課税対象額）
- `source_type`, `source_id`（UNIQUE：二重計上防止）
- `meta_json`

用途:
- 所得の発生元（銀行取引IDや株取引ID等）と紐づけて **再実行に強く** 記録

#### `tax_assessments`（週次課税の確定）
- `assessment_id`（PK）
- `user_id`, `period_id`（UNIQUE）
- `total_income`, `taxable_income`, `tax_amount`
- `status`（CHECK: `assessed` / `paid` / `overdue` / `seizure`）
- `due_at`（課税確定時刻）
- `payment_window_end_at`（納付期限: 火曜終日）
- `paid_at`

用途:
- 週次で計算した「税額の請求書」

#### `tax_payments`（納付記録）
- `payment_id`（PK）
- `assessment_id`（FK, CASCADE）
- `bank_transaction_id`（FK -> `transactions.transaction_id`, SET NULL）
- `amount`, `created_at`

用途:
- 納付が銀行振込と整合するよう、取引IDでリンク

---

### 2-2. ローン（Loans）テーブル

SQL: `migrations/create_loan_system.sql`

#### `loans`
- `loan_id`（PK）
- `user_id`
- `principal`（元本）
- `outstanding_balance`（残債：利息込みで日次増加/返済で減少）
- `status`（CHECK: `active` / `resolved`）
- `interest_weekly_rate`（生の計算結果）
- `interest_weekly_rate_cap_applied`（上限適用後）
- `late_interest_weekly_rate`（遅延損害金：デフォルト週20%）
- `autopay_account_id`（自動引落口座, FK -> accounts）
- `autopay_amount`（日次の引落額、デフォルト1000）
- `last_autopay_attempt_at`, `autopay_failed_since`

用途:
- 現在の借金状態（残債、利率、延滞状態）を単一レコードで管理

#### `loan_payments`
- `payment_id`（PK）
- `loan_id`（FK, CASCADE）
- `bank_transaction_id`（FK -> transactions, SET NULL）
- `amount`, `paid_at`, `created_at`

用途:
- 返済履歴（銀行取引IDで整合）

---

### 2-3. 回収/信用情報（Collections）テーブル

SQL: `migrations/create_tax_and_collections_system.sql`

#### `credit_profile`（信用情報）
- `user_id`（PK）
- `is_blacklisted`（デフォルト false）
- `blacklisted_at`, `blacklisted_reason`

用途:
- 「借入可否」に直接使う信用フラグ

#### `collections_cases`（回収ケース：税/ローン共通）
- `case_id`（PK）
- `user_id`
- `case_type`（CHECK: `tax` / `loan`）
- `reference_id`（税: assessment_id / ローン: loan_id）
- `status`（CHECK: `open` / `in_payment_window` / `overdue` / `seizure` / `resolved`）
- `due_at`, `payment_window_end_at`（主に tax 用）
- `overdue_started_at`, `blacklisted_at`, `seizure_started_at`, `resolved_at`
- `last_inline_notice_at`, `last_push_notice_at`, `next_retry_at`, `retry_count`, `push_notice_count`

用途:
- 税/ローンの「回収フェーズ」を共通管理し、日次処理で状態を進める

#### `collections_accruals`（日次増分：延滞税/利息など）
- `accrual_type`（CHECK: `tax_penalty` / `loan_interest` / `loan_late_interest`）
- `amount`, `principal_base`, `start_date`, `end_date`, `days`

用途:
- 延滞時の増分を監査可能な形で保存（算出根拠の日付範囲を保持）

#### `collections_events`（監査ログ）
- `event_type`, `note`, `meta_json`, `created_at`

用途:
- 「いつ何が起きたか」を後追い可能にする（ケース作成・延滞化・ブラック化・差押え等）

---

### 2-4. DB権限

`migrations/grant_tax_loan_collections_privileges.sql` により、新規テーブル群へ `PUBLIC` にCRUD権限を付与しています。

- 本番で「マイグレーション実行ユーザー」と「アプリ接続ユーザー」が異なる場合、権限不足で runtime が落ちるのを回避する意図
- 必要に応じて `PUBLIC` をアプリ用ロールへ置換推奨

---

## 3. 税（Tax）実装詳細

### 3-1. 所得イベントの記録（台帳）

実装: `apps/tax/tax_service.py`

- 入口: `record_income_event()`
  - `(source_type, source_id)` を UNIQUE として二重登録を防止
- 用途別ラッパ:
  - `record_work_income()`
  - `record_dividend_income()`
  - `record_stock_sale_profit()`（利益がプラスの場合のみ課税対象に計上）
  - `record_gamble_cashout_income()`（換金額・原価・特別控除を元に課税額を計算）

### 3-2. 週次課税の確定

実装: `assess_weekly_taxes_and_autopay()`

- 集計期間（前週）
  - `get_tax_week_bounds_for_assessment()` で `[start_at, end_at)` を計算
  - コメント上の仕様: 「日曜15:01を締め」として半開区間で管理

- 税額計算
  - `compute_tax_amount(weekly_income)`
  - 非課税閾値・1000円未満切捨て・税率表（段階課税）を適用

- `tax_assessments` 作成
  - 所得イベントが存在した `user_id` を対象
  - `tax_amount == 0` の場合は `paid` 扱い（即時完了）
  - `tax_amount > 0` の場合は `assessed` とし、回収ケース（税）を作成
    - `apps/collections/collections_service.ensure_tax_case_for_assessment()`

### 3-3. 自動納付 / 手動納付

- 自動納付
  - `tax_profiles.tax_account_id` が設定されている場合、銀行振込を実行
  - 成功したら `tax_payments` を作成し `tax_assessments.status = paid`
  - 回収ケース（tax）も `resolved` に更新

- 手動納付
  - `pay_latest_unpaid_tax(user_id)` が直近の `assessed` を対象に実行
  - 納税口座未設定の場合はエラー

### 3-4. UI/コマンド

- Flex UI（推奨導線）: `?税`
  - 入口: `apps/tax/ui.py` → `build_dashboard()`
  - 口座登録: 口座選択 → PIN確認（`verify_pin_for_account`）
  - 手動納税: postback `action=tax_pay`

- テキストコマンド: `?納税 ...`
  - 実装: `apps/tax/commands.py`
  - `?納税 設定 001-1234567`
  - `?納税 納付`

---

## 4. 借金（ローン）実装詳細

### 4-1. 借入審査（can_borrow）

実装: `apps/loans/loan_service.py`

- ルール（概略）
  - 最低借入額: `LOAN_MIN_PRINCIPAL`（デフォルト 10,000）
  - ブラックリストなら借入不可（`apps/collections/collections_service.is_blacklisted`）
  - 前週所得が0なら借入不可（`apps/tax/tax_service.get_prev_week_total_income`）
  - 借入上限: `前週所得 × LOAN_MAX_MULTIPLIER`（デフォルト 5）
    - ただし最低上限額 `LOAN_MAX_MIN_AMOUNT`（デフォルト 30,000）を下回らない

- 利率
  - `compute_interest_rate(principal, prev_week_income)`
  - `(principal / prev_income) * LOAN_INTEREST_FACTOR` をベースに、`LOAN_INTEREST_RATE_CAP` 上限適用

### 4-2. 借入（create_loan）

- DB上で `loans` を作成（status=active, outstanding=principal）
- その後、銀行振込（準備口座 → ユーザー受取口座）を実行
  - 実装は **別トランザクション**（銀行側 `transfer_funds` が独自セッション）
- 振込失敗時は、作成済みローンを `resolved` / `outstanding_balance=0` にして無効化

### 4-3. 日次利息（accrue_daily_interest）

- status=active のローンを対象に日次で残債へ利息を加算
- 通常: `interest_weekly_rate_cap_applied / 7`
- 延滞中（`autopay_failed_since` がある）: `late_interest_weekly_rate / 7`
- 監査ログ:
  - 回収ケース（loan）を `ensure_case` で確保し `collections_events` に `loan_interest_accrued` を追加

### 4-4. 日次自動引落（attempt_autopay_daily）

- `autopay_account_id` から準備口座へ `autopay_amount` を引落（残債より多い場合は残債まで）
- 成功:
  - `loan_payments` 追加
  - 残債更新、完済なら `loans.status=resolved`
  - 回収ケース（loan）を `resolved` に更新

- 失敗:
  - `autopay_failed_since` を設定（初回失敗時）
  - 回収ケース（loan）を `overdue` として作成/更新
  - 個別チャットへ Push（2日に1回、失敗開始から7日以内）

### 4-5. 手動返済（manual_repay）

- ユーザーのデフォルト口座（最初のactive/frozen口座）から準備口座へ送金
- 1000円単位の制約
- 返済後は `autopay_failed_since` を解除（延滞状態をリセット）
- 完済なら回収ケースを `resolved` に更新

### 4-6. UI/コマンド

- Flex UI: `?借金`
  - 借入申請フロー（借入額→口座選択→PIN→契約）
  - 返済フロー（返済額入力）

- テキストコマンド
  - `?借入 50000`
  - `?返済`（状態表示） / `?返済 5000`（返済） / `?返済 設定 001-1234567`（自動引落口座変更）

---

## 5. 回収（Collections）実装詳細

### 5-1. ブラックリスト

実装: `apps/collections/collections_service.py`

- `credit_profile` を `get_or_create_credit_profile()` で確保
- ブラックリスト設定: `set_blacklisted(db, user_id, reason)`

使われ方:
- 借入審査（Loans）で参照し、ブラックなら借入不可

### 5-2. 回収ケース作成

- 税: `ensure_tax_case_for_assessment()`
  - status=`in_payment_window`
  - `due_at` と `payment_window_end_at` を保持

- ローン: `ensure_loan_case_for_loan()`
  - status=`overdue`
  - `overdue_started_at` を失敗開始日時として保持

### 5-3. 日次回収処理（process_collections_daily）

実装: `process_collections_daily()`

対象: status が `in_payment_window` / `overdue` / `seizure` のケース

- 税
  - `payment_window_end_at` を超えたら `overdue`
  - ルール簡略化: **未納税 = 即ブラックリスト**（reason=`tax_overdue`）
  - 延滞税（`tax_penalty`）を日次で `collections_accruals` に積む
  - 延滞開始から `TAX_SEIZURE_DAYS` 日で `seizure`（差押え）

- ローン
  - `overdue_started_at` から 7日経過でブラックリスト（reason=`loan_overdue`）
  - `TAX_SEIZURE_DAYS` 日（デフォルト14日）経過で `seizure`

- 差押え（税/ローン共通）
  - `compute_case_amount_due()`
    - tax: `tax_assessments.tax_amount` + penalties
    - loan: `loans.outstanding_balance` + penalties
  - ユーザーの全口座を走査し、残高があれば凍結（status=`frozen`）しつつ目的口座へ送金
    - tax: `TAX_DEST_ACCOUNT_NUMBER`
    - loan: `LOAN_LENDER_ACCOUNT_NUMBER`

### 5-4. 督促通知（inline notice）

実装: `get_inline_notice_text(user_id)`

- tax: `overdue/seizure` のケースがあれば即表示対象
- loan: overdue開始から **7日以上** で表示対象

呼び出し箇所:
- `apps/auto_reply.py` で、個別チャットの全発言に対して `push_message` 送信

---

## 6. 起動点・イベント導線

- `main.py`
  - Flask起動時に `start_tax_collections_loan_scheduler()` を呼び出し

- `core/handler.py` → `apps/auto_reply.py`
  - MessageEvent（テキスト）/ PostbackEvent を `auto_reply()` に集約
  - `?税` / `?借金` は Flex UI のダッシュボード
  - `?納税` / `?借入` / `?返済` はテキストコマンド
  - Flex UI の PIN/金額入力などは `flex_flow`（sessions）で処理

---

## 7. 設定値（config）

`config.py` に税/ローン/回収の主要パラメータがあります。

- 税
  - `TAX_DEST_ACCOUNT_NUMBER`（納税の振込先）
  - `TAX_NON_TAXABLE_THRESHOLD`（非課税閾値）
  - `TAX_ROUND_UNIT`（課税所得切捨単位）
  - `TAX_BRACKETS`（税率表）
  - `TAX_PENALTY_WEEKLY_RATE`（延滞税の週率）
  - `TAX_SEIZURE_DAYS`（差押えまでの日数）

- ローン
  - `LOAN_MIN_PRINCIPAL`（最低借入額）
  - `LOAN_MAX_MULTIPLIER`（借入上限倍率）
  - `LOAN_INTEREST_FACTOR` / `LOAN_INTEREST_RATE_CAP`（通常利率の算出/上限）
  - `LOAN_LATE_WEEKLY_RATE`（遅延損害金の週率）
  - `LOAN_LENDER_ACCOUNT_NUMBER`（貸付元/回収先口座）

---

## 8. 運用・注意点

- DB権限
  - 権限不足だと `is_blacklisted()` / `get_prev_week_total_income()` などが例外を投げ、借入が拒否されます。
  - 本番は `PUBLIC` ではなくアプリ用ロールに置換推奨。

- 送金とDB整合性
  - ローンの発行や納税は「DB更新」と「銀行送金」が別トランザクションです。
  - 失敗時の補正は入っていますが、完全な分散トランザクションではないため、ログ/監査（collections_events）を活用して追跡してください。

- 差押え時の口座凍結
  - 差押え処理は口座を `frozen` にします。解除ルールが必要なら別途仕様化が必要です。

---

## 9. 仕様変更・拡張ポイント

- 税率表/閾値/差押え日数は `config.py` のみで調整可能
- 所得カテゴリを増やす場合
  - `tax_income_events` に `category` を追加し、`record_*` 系の関数を増設する
- 回収の高度化（例: next_retry_at, notice回数制御）
  - `collections_cases` にフィールドはあるため、`process_collections_daily()` にロジック追加が可能
- ローンの複数本管理
  - 現状は「最新activeを優先」するUI/コマンドが多い（`order_by(desc).limit(1)`）。複数本にするならUI/コマンドの選択導線が必要
