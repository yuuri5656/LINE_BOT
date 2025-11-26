# ショップ＆チップシステム設計書

## 📋 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [データベース設計](#データベース設計)
- [システムフロー](#システムフロー)
- [API仕様](#api仕様)
- [コマンド一覧](#コマンド一覧)
- [セットアップ手順](#セットアップ手順)
- [拡張ガイド](#拡張ガイド)

---

## 概要

### 背景
ミニゲームの金銭取引において、従来は銀行口座を直接使用していたため、以下の課題がありました：
- 1ゲーム（4人）で約70クエリ + 9トランザクション発生
- 複雑なエラーハンドリング（個別トランザクションと手動返金）
- 銀行システムとゲームシステムの密結合

### 解決策
**チップベースのゲーム通貨システム**を導入：
1. ユーザーは銀行口座からショップでチップを購入
2. ミニゲームはチップで参加（銀行システムから分離）
3. バッチ処理により、4人ゲームで約18クエリ + 3トランザクション（74%削減）

### 主要機能
- 💰 **チップ管理**: 残高確認、購入、送信、履歴表示
- 🛒 **ショップ**: カテゴリ別商品表示、購入処理、EAV属性対応
- 🎮 **ゲーム統合**: チップロック/分配のバッチ処理
- 💳 **支払い口座**: ユーザーごとの決済用口座登録

---

## アーキテクチャ

### システム構成図

```
┌──────────────────────────────────────────────────────────┐
│                      ユーザー                            │
│                         │                                │
│           ┌─────────────┼─────────────┐                  │
│           │             │             │                  │
│      [銀行口座]    [チップ残高]   [ミニゲーム]           │
└───────┬────────────┬─────────────┬───────────────────────┘
        │            │             │
        │ 振替API    │ チップAPI   │ ゲームAPI
        ↓            ↓             ↓
┌────────────────────────────────────────────────────────────┐
│                    Banking System (既存)                   │
│  - 口座管理                                                │
│  - 振り込み処理                                            │
│  - バッチ出入金 (batch_withdraw/deposit)                   │
└────────┬───────────────────────────────────────────────────┘
         │ 銀行振替
         ↓
┌────────────────────────────────────────────────────────────┐
│                    Shop System (新規)                      │
│  - 商品カタログ管理 (EAVパターン)                          │
│  - 支払い口座登録                                          │
│  - 購入処理オーケストレーション                            │
│  ├─ 銀行振替 → ショップ運営口座                            │
│  └─ チップクレジット → ユーザー                            │
└────────┬───────────────────────────────────────────────────┘
         │ チップクレジット
         ↓
┌────────────────────────────────────────────────────────────┐
│                   Chip System (新規)                       │
│  - チップ残高管理                                          │
│  - トランザクション記録                                    │
│  - バッチロック/分配                                       │
└────────┬───────────────────────────────────────────────────┘
         │ ゲーム参加
         ↓
┌────────────────────────────────────────────────────────────┐
│                  Minigame System (改修)                    │
│  - チップベースの参加費徴収                                │
│  - チップベースの賞金分配                                  │
└────────────────────────────────────────────────────────────┘
```

### レイヤー分離の原則

| レイヤー | 責務 | 依存方向 |
|---------|------|---------|
| **Banking System** | 法定通貨の管理 | なし（独立） |
| **Shop System** | 商品販売と決済 | Banking（支払い）→ Chip（クレジット） |
| **Chip System** | ゲーム内通貨管理 | なし（独立） |
| **Minigame System** | ゲームロジック | Chip（参加費・賞金） |

**重要**: 各システムは明確に分離され、APIを通じてのみ連携します。

---

## データベース設計

### ER図

```
┌─────────────────┐
│  bank_accounts  │ (既存)
│  - user_id      │
│  - balance      │
└────────┬────────┘
         │ 1:1
         ↓
┌──────────────────────┐
│ shop_payment_accounts│ (新規)
│ - user_id (PK)       │
│ - account_number     │
│ - branch_code        │
│ - account_name       │
│ - created_at         │
└──────────────────────┘
         │
         │ N:1 (購入履歴)
         ↓
┌──────────────────┐       ┌────────────────────┐
│  shop_purchases  │       │   minigame_chips   │
│ - purchase_id    │       │ - user_id (PK)     │
│ - user_id        │       │ - balance          │
│ - item_id ───────┼──┐    │ - locked_balance   │
│ - amount_paid    │  │    │ - updated_at       │
│ - purchased_at   │  │    └─────────┬──────────┘
└──────────────────┘  │              │ 1:N
                      │              ↓
        ┌─────────────┘    ┌──────────────────────┐
        ↓                  │  chip_transactions   │
┌──────────────────┐       │ - transaction_id     │
│   shop_items     │       │ - user_id            │
│ - item_id (PK)   │       │ - amount             │
│ - item_code      │       │ - transaction_type   │
│ - name           │       │ - reference_id       │
│ - description    │       │ - created_at         │
│ - price          │       └──────────────────────┘
│ - category       │
│ - is_active      │
└─────────┬────────┘
          │ 1:N
          ↓
┌────────────────────────┐
│ shop_item_attributes   │ (EAVパターン)
│ - attribute_id (PK)    │
│ - item_id (FK)         │
│ - attribute_key        │
│ - attribute_value      │
│ - value_type           │
└────────────────────────┘
```

### テーブル詳細

#### 1. `minigame_chips` - チップ残高管理

```sql
CREATE TABLE minigame_chips (
    user_id VARCHAR(255) PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0,
    locked_balance INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**カラム説明**:
- `balance`: 利用可能なチップ残高
- `locked_balance`: ゲーム参加中でロックされているチップ（二重使用防止）
- `updated_at`: 最終更新日時（自動更新トリガー付き）

**制約**:
```sql
CHECK (balance >= 0 AND locked_balance >= 0)
```

#### 2. `chip_transactions` - チップ取引履歴

```sql
CREATE TABLE chip_transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**transaction_type 種別**:
- `purchase`: ショップでの購入
- `transfer_out`: 他ユーザーへの送信
- `transfer_in`: 他ユーザーからの受信
- `game_bet`: ゲーム参加費（ロック）
- `game_win`: ゲーム勝利報酬
- `game_loss`: ゲーム敗北（没収）
- `game_refund`: ゲームキャンセル時の返金

**インデックス**:
```sql
CREATE INDEX idx_chip_transactions_user_id ON chip_transactions(user_id);
CREATE INDEX idx_chip_transactions_created_at ON chip_transactions(created_at DESC);
```

#### 3. `shop_items` - 商品マスタ

```sql
CREATE TABLE shop_items (
    item_id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**category 種別**:
- `casino_chips`: カジノチップパック
- `special_items`: スペシャルアイテム（将来拡張用）
- `boosters`: ブースター（経験値倍率等）

#### 4. `shop_item_attributes` - 商品属性（EAVパターン）

```sql
CREATE TABLE shop_item_attributes (
    attribute_id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES shop_items(item_id),
    attribute_key VARCHAR(100) NOT NULL,
    attribute_value TEXT NOT NULL,
    value_type VARCHAR(20) NOT NULL
);
```

**EAVパターンの利点**:
- 商品タイプごとに異なる属性を柔軟に定義可能
- テーブル構造の変更なしで新属性追加可能

**共通属性例**:

| item_code | attribute_key | attribute_value | value_type |
|-----------|---------------|-----------------|-----------|
| chip_pack_100 | chip_amount | 100 | integer |
| chip_pack_100 | bonus_chip | 0 | integer |
| chip_pack_500 | chip_amount | 500 | integer |
| chip_pack_500 | bonus_chip | 50 | integer |
| exp_booster_7d | boost_rate | 2.0 | float |
| exp_booster_7d | duration_days | 7 | integer |

**インデックス**:
```sql
CREATE INDEX idx_shop_item_attributes_item_id ON shop_item_attributes(item_id);
CREATE UNIQUE INDEX idx_shop_item_attributes_unique ON shop_item_attributes(item_id, attribute_key);
```

#### 5. `shop_payment_accounts` - 支払い用口座登録

```sql
CREATE TABLE shop_payment_accounts (
    user_id VARCHAR(255) PRIMARY KEY,
    account_number VARCHAR(7) NOT NULL,
    branch_code VARCHAR(3) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**用途**: ユーザーが所有する銀行口座を決済用として登録（ワンタイム認証済み）

#### 6. `shop_purchases` - 購入履歴

```sql
CREATE TABLE shop_purchases (
    purchase_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id INTEGER NOT NULL REFERENCES shop_items(item_id),
    item_name VARCHAR(255) NOT NULL,
    amount_paid INTEGER NOT NULL,
    chips_received INTEGER,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## システムフロー

### 1. チップ購入フロー

```
[ユーザー]
    │
    │ 1. "?ショップ" コマンド
    ↓
[Shop Commands]
    │
    │ 2. カテゴリカルーセル表示
    ↓
[ユーザー] ← FlexMessage
    │
    │ 3. カテゴリ選択 (postback)
    ↓
[Shop Commands]
    │
    │ 4. 商品一覧表示（EAV属性付き）
    ↓
[ユーザー] ← FlexMessage
    │
    │ 5. 商品購入ボタン (postback)
    ↓
[Shop Commands]
    │
    ├─ 5-1. 支払い口座登録済み？
    │   NO → 口座登録フロー開始
    │   YES ↓
    │
    │ 6. purchase_item() 呼び出し
    ↓
[Shop Service]
    │
    ├─ 7-1. 商品情報取得（EAV属性含む）
    │
    ├─ 7-2. 支払い口座情報取得
    │
    ├─ 7-3. 銀行振替実行
    │        ユーザー口座 → ショップ運営口座
    │        (banking_api.transfer_funds)
    │
    └─ 7-4. チップクレジット
             (chip_service.purchase_chips)
    ↓
[Chip Service]
    │
    ├─ 8-1. トランザクション開始
    │
    ├─ 8-2. minigame_chips.balance 更新
    │
    ├─ 8-3. chip_transactions 記録
    │
    ├─ 8-4. shop_purchases 記録
    │
    └─ 8-5. コミット
    ↓
[ユーザー] ← 購入完了FlexMessage
```

### 2. ゲーム参加フロー（チップロック）

```
[グループチャット]
    │
    │ 1. "?じゃんけん" コマンド
    ↓
[Game Commands]
    │
    │ 2. セッション作成（参加費: 100枚）
    ↓
[ユーザーA/B/C/D]
    │
    │ 3. "?参加" コマンド
    ↓
[Minigames] join_game_session()
    │
    ├─ 4-1. check_chip_balance(user_id, 100)
    │        残高不足 → "ショップで購入してください"
    │        残高OK ↓
    │
    └─ 4-2. プレイヤーリスト追加
    ↓
[ホスト] "?スタート" コマンド
    ↓
[Minigames] start_game_session()
    │
    ├─ 5-1. batch_lock_chips() 呼び出し
    │        {userA: 100, userB: 100, userC: 100, userD: 100}
    ↓
[Chip Service] batch_lock_chips()
    │
    ├─ 5-2. トランザクション開始
    │
    ├─ FOR EACH user:
    │   ├─ balance >= 100? チェック
    │   ├─ balance -= 100
    │   ├─ locked_balance += 100
    │   └─ chip_transactions 記録 (game_bet)
    │
    ├─ 5-3. コミット（全員成功）
    │        または ロールバック（1人でも失敗）
    │
    └─ 5-4. 成功/失敗リスト返却
    ↓
[Minigames]
    │
    └─ 5-5. 失敗者をセッションから除外
    ↓
[グループチャット] ← ゲーム開始FlexMessage
```

### 3. ゲーム終了フロー（チップ分配）

```
[ゲーム終了]
    │
    │ 順位確定: 1位 userA, 2位 userB, 3位 userC, 4位 userD
    ↓
[Minigames] finish_game_session()
    │
    ├─ 1. 賞金計算（固定分配方式）
    │    総額: 400枚
    │    手数料10%: 40枚
    │    分配可能額: 360枚
    │
    │    1位: 260枚 (65%)
    │    2位:  72枚 (20%)
    │    3位:  36枚 (10%)
    │    4位:  18枚 ( 5%)
    │    ───────────────
    │    合計: 386枚 (差額は誤差調整で1位に加算)
    │
    ├─ 2. distribute_chips() 呼び出し
    │    payouts = {
    │        userA: 234, userB: 72,
    │        userC: 36, userD: 18
    │    }
    │    fee = 40
    ↓
[Chip Service] distribute_chips()
    │
    ├─ 3-1. トランザクション開始
    │
    ├─ FOR EACH user:
    │   ├─ locked_balance -= 100 (ロック解除)
    │   ├─ balance += payout額
    │   └─ chip_transactions 記録 (game_win/loss)
    │
    ├─ 3-2. 手数料をショップ運営用チップ口座に転送
    │
    ├─ 3-3. コミット
    │
    └─ 3-4. 分配完了通知
    ↓
[グループチャット] ← 結果FlexMessage（順位・収支表示）
```

---

## API仕様

### Chip Service API (`apps/banking/chip_service.py`)

#### `get_chip_balance(user_id: str) -> int`
チップ残高を取得

**戻り値**: 利用可能なチップ残高（`balance`）

---

#### `purchase_chips(user_id, total_chips, account_number, branch_code) -> Dict`
チップ購入処理

**パラメータ**:
- `user_id`: ユーザーID
- `total_chips`: 購入チップ数（ボーナス含む）
- `account_number`: 支払い元口座番号
- `branch_code`: 支払い元支店番号

**戻り値**:
```python
{
    'status': 'success',
    'chips_credited': 550,
    'new_balance': 1234
}
```

---

#### `transfer_chips(from_user_id, to_user_id, amount, notes) -> Dict`
チップ送信

**パラメータ**:
- `from_user_id`: 送信者ID
- `to_user_id`: 受信者ID
- `amount`: 送信枚数
- `notes`: メモ（任意）

**戻り値**:
```python
{
    'status': 'success',
    'transferred_amount': 100,
    'new_balance': 900
}
```

---

#### `batch_lock_chips(user_ids, lock_amounts, game_id) -> Dict`
バッチチップロック（ゲーム開始時）

**パラメータ**:
- `user_ids`: ユーザーIDリスト
- `lock_amounts`: `{user_id: lock_amount}` の辞書
- `game_id`: ゲームセッション識別子

**戻り値**:
```python
{
    'success': True,
    'locked': ['user1', 'user2', 'user3'],
    'failed': ['user4']  # 残高不足
}
```

**動作**:
- **アトミック**: 全員成功 or 全員ロールバック
- `balance` から `locked_balance` に移動
- 失敗者リストを返却（呼び出し側でセッションから除外）

---

#### `distribute_chips(user_payouts, game_id, fee_amount) -> Dict`
バッチチップ分配（ゲーム終了時）

**パラメータ**:
- `user_payouts`: `{user_id: payout_amount}` の辞書
- `game_id`: ゲームセッション識別子
- `fee_amount`: 手数料（運営口座に転送）

**戻り値**:
```python
{
    'success': True,
    'distributed': ['user1', 'user2', 'user3', 'user4']
}
```

**動作**:
- `locked_balance` を解除
- `balance` に賞金を加算
- 手数料を運営用チップ口座に転送

---

#### `get_chip_history(user_id, limit=10) -> List[Dict]`
チップ取引履歴

**戻り値**:
```python
[
    {
        'transaction_id': 123,
        'amount': 100,
        'transaction_type': 'purchase',
        'timestamp': datetime(...)
    },
    ...
]
```

---

### Shop Service API (`apps/shop/shop_service.py`)

#### `get_shop_categories() -> List[Dict]`
ショップカテゴリ一覧

**戻り値**:
```python
[
    {
        'code': 'casino_chips',
        'name': 'カジノチップ',
        'icon': '🎰',
        'description': 'ミニゲームで使用できるチップ'
    },
    ...
]
```

---

#### `get_items_by_category(category: str) -> List[Dict]`
カテゴリ別商品一覧（EAV属性含む）

**戻り値**:
```python
[
    {
        'item_id': 1,
        'name': 'チップパック100',
        'description': '100枚のチップ',
        'price': 1000,
        'attributes': {
            'chip_amount': 100,
            'bonus_chip': 0
        }
    },
    ...
]
```

**属性の型変換**: `value_type` に基づき自動変換（integer, float, boolean, string）

---

#### `register_payment_account(db, user_id, branch_code, account_number, account_name, pin_code) -> Dict`
支払い用口座登録

**パラメータ**:
- `branch_code`: 支店番号（3桁）
- `account_number`: 口座番号（7桁）
- `account_name`: 口座名義
- `pin_code`: 暗証番号（4桁、認証用）

**戻り値**:
```python
{
    'status': 'success',
    'branch_code': '001',
    'account_number': '1234567',
    'account_name': 'ヤマダタロウ'
}
```

**セキュリティ**:
- `check_pin()` で暗証番号を検証
- 認証成功後、暗証番号は保存せず

---

#### `purchase_item(db, user_id, item_id) -> Dict`
商品購入処理

**戻り値**:
```python
{
    'status': 'success',
    'item_name': 'チップパック500',
    'chips_received': 550,  # ボーナス含む
    'new_chip_balance': 1784
}
```

**内部フロー**:
1. 商品情報取得（EAV属性含む）
2. 支払い口座情報取得
3. 銀行振替実行（ユーザー → ショップ運営口座）
4. チップクレジット（`chip_service.purchase_chips`）
5. 購入履歴記録

---

## コマンド一覧

### ショップコマンド

| コマンド | 場所 | 説明 |
|---------|------|------|
| ?ショップ | 個別/グループ | ショップホーム画面を表示 |
| ?チップ残高 | 個別/グループ | 現在のチップ残高を表示 |
| ?チップ履歴 | 個別/グループ | 最新10件の取引履歴を表示 |
| ?チップ送信 | 個別 | 他ユーザーへチップ送信（未実装） |

| ?チップ換金 | 個別 | チップを銀行口座に換金（100%） |

### ショップPostbackアクション

| アクション | データ形式 | 説明 |
|-----------|-----------|------|
| ショップホーム | action=shop_home | カテゴリカルーセル表示 |
| カテゴリ選択 | action=shop_category&category=casino_chips | 商品一覧表示 |
| 商品購入 | action=shop_buy&item_id=1 | 購入処理実行 |
| 口座登録開始 | action=register_payment_account | 支払い口座登録フロー |

---

## チップ換金機能

### 概要

- ?チップ換金 <枚数> で、登録済みの支払い口座に1チップ=1JPYで換金できます（換金率100%）。
- 換金時は利用可能なチップのみ対象。ロック中（ゲーム参加中）は換金不可。
- 振込失敗時は自動でチップ返金されます。

### コマンド例

```
?チップ換金 100
```

### 画面例

```
✅ チップ換金完了

換金枚数: 100枚
振込額: 100 JPY
残りのチップ: 450枚

※登録済みの口座に振り込まれました
```

### 仕様詳細

- 換金先は「?ショップ」で登録した支払い口座。
- 換金履歴は「?チップ履歴」に `redeem` として記録。
- 失敗時は `redeem_failed` で返金履歴も記録。

### API

#### `redeem_chips(user_id: str, amount: int) -> Dict`

| パラメータ | 内容 |
|---|---|
| user_id | ユーザーID |
| amount | 換金するチップ枚数 |

**戻り値例**:
```python
{
    'success': True,
    'new_balance': 450,
    'amount_received': 100
}
```

**失敗時**:
```python
{
    'success': False,
    'error': '換金先口座が登録されていません。先に「?ショップ」から支払い口座を登録してください。'
}
```

### セキュリティ・運用上の注意

- 換金はアトミックに処理。銀行振込失敗時は即時チップ返金。
- ゲーム参加中のロック分は換金不可。
- 換金履歴は全て `chip_transactions` テーブルに記録。

### 使用例

```
# 1. チップ残高確認
ユーザー: ?チップ残高
BOT: 💰 現在のチップ残高: 550枚

# 2. 換金方法確認
ユーザー: ?チップ換金
BOT: 使用方法: ?チップ換金 <枚数>...

# 3. 100枚換金
ユーザー: ?チップ換金 100
BOT: ✅ チップ換金完了
     換金枚数: 100枚
     振込額: 100 JPY
     残りのチップ: 450枚

# 4. 履歴確認
ユーザー: ?チップ履歴
BOT: 📊 チップ取引履歴
     💵 11/26 14:30 換金 -100枚
     ✅ 11/26 10:00 購入 +550枚
```

### ゲームコマンド（チップ対応）

| コマンド | 場所 | 説明 |
|---------|------|------|
| ?じゃんけん | グループ | じゃんけんゲーム募集開始（チップ参加費制） |
| ?参加 | グループ | ゲームに参加（チップ残高チェック） |

---

## セットアップ手順

### 1. データベースマイグレーション

```bash
# PostgreSQLに接続
psql -U your_user -d your_database

# マイグレーションSQL実行
\i d:/all/my-app/line_bot/LINE_BOT/migrations/create_chip_and_shop_system.sql
```

**確認**:
```sql
-- テーブル存在確認
\dt minigame_chips
\dt chip_transactions
\dt shop_items
\dt shop_item_attributes
\dt shop_payment_accounts
\dt shop_purchases

-- 初期データ確認
SELECT * FROM shop_items;
SELECT * FROM shop_item_attributes;
```

### 2. ショップ運営口座の作成

```sql
-- 運営用銀行口座を作成
INSERT INTO bank_accounts (user_id, account_number, branch_num, balance, account_name)
VALUES (
    'SHOP_OPERATIONS',
    '9999999',
    '999',
    0,
    'ショップ運営'
);
```

**重要**: `shop_service.py` の `SHOP_OPERATIONS_ACCOUNT` 定数と一致させること

### 3. アプリケーション再起動

```bash
# PowerShellの場合
cd d:\all\my-app\line_bot\LINE_BOT
python main.py
```

### 4. 動作確認

#### チップ購入テスト
1. LINE個別チャットで「?ショップ」
2. カテゴリ選択（例: カジノチップ）
3. 商品選択（例: チップパック100）
4. 支払い口座登録（初回のみ）
5. 購入完了確認

#### ゲーム参加テスト
1. グループチャットで「?じゃんけん」
2. 「?参加」（チップ残高チェック）
3. ホストが「?スタート」（バッチロック）
4. 手を提出してゲーム終了（バッチ分配）

---

## 拡張ガイド

### 新商品の追加

#### 1. 商品レコードを追加
```sql
INSERT INTO shop_items (item_code, name, description, price, category, sort_order)
VALUES (
    'exp_booster_30d',
    '経験値ブースター（30日）',
    '30日間、経験値が3倍になります',
    5000,
    'boosters',
    10
);
```

#### 2. EAV属性を追加
```sql
-- item_id=4 と仮定
INSERT INTO shop_item_attributes (item_id, attribute_key, attribute_value, value_type)
VALUES
    (4, 'boost_rate', '3.0', 'float'),
    (4, 'duration_days', '30', 'integer'),
    (4, 'target_stat', 'exp', 'string');
```

#### 3. 処理ロジック追加（必要に応じて）
```python
# apps/shop/shop_service.py

def _purchase_booster_item(db, user_id: str, item, payment_info: Dict):
    """ブースター購入処理"""
    boost_rate = get_item_attribute(item.item_id, 'boost_rate', 1.0)
    duration_days = get_item_attribute(item.item_id, 'duration_days', 0)
    
    # ユーザーのブースター状態を更新
    # （実装は要件次第）
    
    return {
        'status': 'success',
        'message': f'{duration_days}日間の{boost_rate}倍ブースターを適用しました'
    }
```

### 新カテゴリの追加

#### 1. `get_shop_categories()` に追加
```python
def get_shop_categories():
    return [
        # ... 既存カテゴリ ...
        {
            'code': 'cosmetics',
            'name': 'コスメティック',
            'icon': '✨',
            'description': 'プロフィール装飾アイテム'
        }
    ]
```

#### 2. `purchase_item()` に処理分岐追加
```python
def purchase_item(db, user_id: str, item_id: int):
    # ...
    category = item.category
    
    if category == 'cosmetics':
        result = _purchase_cosmetic_item(db, user_id, item, payment_info)
    # ...
```

### チップ送信機能の実装例

```python
# apps/shop/commands.py

def handle_chip_transfer_command(user_id: str, text: str, db):
    """?チップ送信 @user_id 100"""
    parts = text.strip().split()
    
    if len(parts) != 3:
        return TextSendMessage(text="使用方法: ?チップ送信 @ユーザーID 枚数")
    
    to_user_id = parts[1].lstrip('@')
    try:
        amount = int(parts[2])
    except ValueError:
        return TextSendMessage(text="枚数は整数で指定してください")
    
    result = transfer_chips(user_id, to_user_id, amount, notes="ユーザー送信")
    
    if result['status'] == 'success':
        return TextSendMessage(
            text=f"✅ {to_user_id} に {amount}枚のチップを送信しました\n"
                 f"残高: {result['new_balance']}枚"
        )
    else:
        return TextSendMessage(text=f"❌ {result['message']}")
```

### EAV属性の型拡張

現在サポート: `integer`, `float`, `boolean`, `string`

新しい型を追加する場合:
```python
# apps/shop/shop_service.py

def get_item_attribute(item_id: int, key: str, default=None):
    # ...
    elif attr.value_type == 'json':
        import json
        return json.loads(attr.attribute_value)
    elif attr.value_type == 'date':
        from datetime import datetime
        return datetime.fromisoformat(attr.attribute_value)
    # ...
```

---

## トラブルシューティング

### 問題: チップ購入時に「口座が見つかりません」エラー

**原因**: 支払い口座が未登録、または口座情報が不正

**解決策**:
1. 「?ショップ」→ 商品購入 → 口座登録フローを実施
2. データベース確認:
```sql
SELECT * FROM shop_payment_accounts WHERE user_id = 'U1234...';
```

### 問題: ゲーム開始時に「チップのロックに失敗」

**原因**: 参加者の誰かがチップ残高不足

**解決策**:
- エラーメッセージに失敗者リストが表示される
- 該当ユーザーに「?チップ残高」で確認してもらう
- 「?ショップ」でチップ購入を案内

### 問題: 購入履歴が記録されない

**原因**: `shop_purchases` テーブルへの INSERT が失敗

**デバッグ**:
```python
# apps/banking/chip_service.py の purchase_chips() にログ追加
try:
    purchase_record = ShopPurchase(...)
    db.add(purchase_record)
    db.commit()
except Exception as e:
    print(f"[Chip Service] Failed to record purchase: {e}")
    db.rollback()
```

### 問題: EAV属性が取得できない

**原因**: `value_type` が不正、または属性が存在しない

**確認**:
```sql
SELECT * FROM shop_item_attributes WHERE item_id = 1;
```

**デフォルト値を設定**:
```python
chip_amount = get_item_attribute(item.item_id, 'chip_amount', 0)  # デフォルト0
```

---

## パフォーマンス指標

### バッチ処理による最適化効果

| 項目 | 従来（銀行口座） | 現在（チップ） | 改善率 |
|-----|-----------------|-----------------|--------|
| クエリ数 | 約28件（各ユーザー7件） | 約7件（バッチ処理） | 75%削減 |
| トランザクション数 | 4件（各ユーザー1件） | 1件（一括） | 75%削減 |
| クエリ数 | 約36件（各ユーザー9件） | 約9件（バッチ処理） | 75%削減 |
| トランザクション数 | 4件 + 1件（手数料） | 1件（一括） | 80%削減 |
| クエリ数 | 約70件 | 約18件 | 74%削減 |
| トランザクション数 | 9件 | 3件 | 67%削減 |

### スケーラビリティ

- **同時接続**: チップシステムは銀行システムから独立しているため、ゲーム参加が銀行トランザクションに影響しない
- **ロック競合**: `locked_balance` により二重使用を防止、ゲーム中の他操作は通常の `balance` で継続可能
- **データ増加**: `chip_transactions` テーブルはパーティショニング可能（月次等）

---

## セキュリティ考慮事項

### 1. 暗証番号の取り扱い
- ✅ **保存しない**: `register_payment_account()` で認証後、暗証番号は破棄
- ✅ **通信経路**: LINEプラットフォーム経由（TLS暗号化）
- ⚠️ **推奨**: 将来的にはOAuth等の外部認証を検討

### 2. チップの二重使用防止
- ✅ **ロック機構**: ゲーム参加中は `locked_balance` に移動、他用途に使用不可
- ✅ **アトミック処理**: バッチロック/分配は単一トランザクション内で実行

### 3. 不正購入対策
- ✅ **口座認証**: 初回登録時に暗証番号で本人確認
- ✅ **トランザクション記録**: 全ての購入・使用履歴を `chip_transactions` に記録
- ⚠️ **推奨**: 異常な購入パターン検知（短時間大量購入等）

### 4. SQL Injection対策
- ✅ **ORM使用**: SQLAlchemyによるパラメータバインディング
- ✅ **バリデーション**: 入力値の型・長さチェック

---

## ライセンスと謝辞

本システムは、ミニゲームの経済システム最適化プロジェクトの一環として設計・実装されました。

**設計思想**:
- **関心の分離**: Banking / Shop / Chip / Minigame の各層を明確に分離
- **拡張性**: EAVパターンによる柔軟な商品属性管理
- **パフォーマンス**: バッチ処理によるDB負荷削減
- **保守性**: 明確なAPI境界とトランザクション管理

---

**最終更新**: 2025年11月26日  
**バージョン**: 1.0.0
