# 銀行システム・ミニゲーム金銭取引関連の大幅修正

## 修正概要

このアップデートでは、銀行システムとミニゲームの金銭取引機能を大幅に改修しました。

## 主な変更点

### 1. 顧客情報管理の実装

- **customersテーブル**: 顧客の基本情報(フルネーム、生年月日、user_id)を保存
- **customer_credentialsテーブル**: 暗証番号をArgon2でハッシュ化して保存
- accountsテーブルにcustomer_idカラムを追加し、顧客情報と紐付け

#### 実装ファイル
- `apps/minigame/main_bank_system.py`: CustomerとCustomerCredentialのORMモデルを追加
- `apps/minigame/bank_service.py`:
  - `hash_pin()`: Argon2による暗証番号のハッシュ化
  - `verify_pin()`: ハッシュ化された暗証番号の検証

### 2. 口座開設処理の強化

口座開設時に顧客情報と認証情報を同時に登録するように変更しました。

#### 実装ファイル
- `apps/minigame/bank_service.py`: `create_account_optimized()`関数を修正
  - 顧客情報の作成・登録
  - 暗証番号のハッシュ化と保存
  - トランザクション内で一括処理

### 3. 口座種別の追加

当座預金(current)を口座種別として追加しました。

#### 実装ファイル
- `apps/minigame/main_bank_system.py`: account_type_enumに'current'を追加
- `apps/minigame/bank_reception.py`: 口座開設フローで「当座預金」を選択可能に
- `apps/minigame/bank_service.py`: account_type_mappingに当座預金を追加

#### データベースマイグレーション
```sql
-- db_migrations/add_current_account_type.sql
ALTER TYPE account_type ADD VALUE IF NOT EXISTS 'current';
```

### 4. ミニゲーム参加認証APIの実装

ミニゲーム参加時に銀行システムの顧客情報を使用した認証機能を追加しました。

#### 実装ファイル
- `apps/minigame/bank_service.py`: `authenticate_customer()`関数
  - 認証要素: user_id、フルネーム、生年月日、暗証番号
  - Argon2による暗証番号検証

#### 使用例
```python
from apps.minigame.bank_service import authenticate_customer

# ミニゲーム参加時の認証
is_authenticated = authenticate_customer(
    user_id="U1234567890abcdef",
    full_name="山田 太郎",
    date_of_birth="1990-01-01",
    pin_code="1234"
)
```

### 5. 支払い失敗判定バグの修正

ミニゲーム開始時の参加費徴収処理で、変数名と処理ロジックの不整合を修正しました。

#### 実装ファイル
- `apps/minigame/minigames.py`: `start_game_session()`関数
  - `refunded`変数を`failed`に変更(まだ引き落としていないユーザーを明確化)
  - 支払い失敗時のログ出力を改善

### 6. 取引履歴の自動記録

出入金時に必ずtransactionsテーブルとtransaction_entriesテーブルに記録されるように変更しました。

#### 実装ファイル
- `apps/minigame/bank_service.py`: 
  - `withdraw_from_user()`: 出金時にtransactionレコードとentryを作成
  - `deposit_to_user()`: 入金時にtransactionレコードとentryを作成

#### トランザクション記録の詳細
- **出金(withdrawal)**:
  - `from_account_id`: 出金元口座
  - `to_account_id`: NULL
  - `type`: 'withdrawal'
  - `entry_type`: 'debit'

- **入金(deposit)**:
  - `from_account_id`: NULL
  - `to_account_id`: 入金先口座
  - `type`: 'deposit'
  - `entry_type`: 'credit'

## 依存パッケージの追加

### requirements.txt
```
argon2-cffi
```

Argon2による暗証番号のハッシュ化に必要なパッケージです。

## セットアップ手順

### 1. パッケージのインストール
```powershell
pip install -r requirements.txt
```

### 2. データベースマイグレーション
```powershell
# PostgreSQLに接続
psql -U <username> -d <database_name>

# ENUMタイプに'current'を追加
\i db_migrations/add_current_account_type.sql
```

### 3. 既存データの移行(必要に応じて)

既存のaccountsテーブルにデータがある場合、customer_idを設定する必要があります。

```sql
-- 既存の口座に対して顧客情報を作成
-- (実際の環境に応じてカスタマイズしてください)
```

## 使用方法

### 口座開設フロー

1. ユーザーが個別チャットで「?口座開設」と送信
2. フルネーム入力
3. 生年月日入力(YYYY-MM-DD形式)
4. 支店選択
5. 口座種別選択(普通預金・当座預金・定期預金)
6. 4桁の暗証番号設定

### ミニゲーム参加フロー

1. 口座開設済みであることが前提
2. グループチャットでゲームに参加
3. 認証が必要な場合、`authenticate_customer()`を使用
4. 参加費の自動引き落とし
5. ゲーム終了後、賞金の自動入金

## セキュリティ向上

- **Argon2ハッシュ化**: 暗証番号を平文で保存せず、Argon2アルゴリズムでハッシュ化
- **ソルト管理**: 各暗証番号に対して一意のソルトを生成
- **認証強化**: 複数の要素(フルネーム、生年月日、暗証番号)での認証

## トラブルシューティング

### argon2インポートエラー
```
ModuleNotFoundError: No module named 'argon2'
```
→ `pip install argon2-cffi` を実行してください

### ENUM型エラー
```
ERROR: invalid input value for enum account_type: "current"
```
→ `db_migrations/add_current_account_type.sql` を実行してください

### 既存口座のcustomer_id NULL エラー
```
ERROR: null value in column "customer_id" violates not-null constraint
```
→ 既存の口座データに対して顧客情報を作成してください

## 今後の拡張予定

- [ ] KYC(本人確認)機能の追加
- [ ] 二要素認証の実装
- [ ] 取引履歴の詳細検索機能
- [ ] 口座間送金機能のUI改善
- [ ] 定期預金の利息計算機能
