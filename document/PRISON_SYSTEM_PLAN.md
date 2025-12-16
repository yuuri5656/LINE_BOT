# 懲役システムと管理者コマンド 実装プラン

## 📋 プラン概要

LINE BOT の既存の銀行・労働システムを拡張して、懲役システムと管理者用コマンドを実装します。

---

## 1. データベーススキーマ設計

### 1.1 新規テーブル: `prison_sentences` (懲役情報)

```sql
CREATE TABLE IF NOT EXISTS prison_sentences (
    sentence_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    start_date DATE NOT NULL,           -- 施行日
    end_date DATE NOT NULL,             -- 釈放日
    initial_days INTEGER NOT NULL,      -- 初期懲役日数
    remaining_days INTEGER NOT NULL,    -- 残り懲役日数
    daily_quota INTEGER NOT NULL,       -- 1日のノルマ（?労働回数）
    completed_today INTEGER DEFAULT 0,  -- 今日の?労働実行回数
    last_work_date DATE,                -- 最後に?労働を実行した日付
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    FOREIGN KEY (user_id) REFERENCES customers(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_prison_user_id ON prison_sentences(user_id);
CREATE INDEX idx_prison_end_date ON prison_sentences(end_date);
```

### 1.2 新規テーブル: `prison_rehabilitation_fund` (犯罪者更生給付金口座)

```sql
CREATE TABLE IF NOT EXISTS prison_rehabilitation_fund (
    fund_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,        -- 準備預金口座と同じ概念の会計用口座
    total_collected NUMERIC(15,2) DEFAULT 0,  -- 累計収集額
    last_distribution_date DATE,        -- 最後に分配した日付
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);
```

### 1.3 新規テーブル: `prison_rehabilitation_distributions` (分配履歴)

```sql
CREATE TABLE IF NOT EXISTS prison_rehabilitation_distributions (
    distribution_id SERIAL PRIMARY KEY,
    distribution_date DATE NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,
    recipient_count INTEGER NOT NULL,
    amount_per_recipient NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_prison_dist_date ON prison_rehabilitation_distributions(distribution_date);
```

### 1.4 既存テーブル: `accounts` の変更

既存の `account_status` ENUM に `'frozen'` ステータスが存在することを確認済み。
- `status = 'frozen'`：懲役中の凍結口座

---

## 2. 懲役システムの実装

### 2.1 新規ファイル: `apps/prison/` ディレクトリ構成

```
apps/prison/
  ├── __init__.py
  ├── commands.py                      # 管理者コマンドハンドラー
  ├── prison_service.py                # 懲役ビジネスロジック
  ├── prison_models.py                 # SQLAlchemy ORM モデル定義
  ├── prison_flex.py                   # Flex メッセージテンプレート
  └── rehabilitation_scheduler.py      # 1日1回の分配スケジューラー
```

### 2.2 主要機能の実装内容

#### A. `prison_service.py` - コア機能

```python
# 懲役を設定する
def sentence_prisoner(
    user_id: str, 
    start_date: date, 
    days: int, 
    daily_quota: int
) -> dict:
    """
    ユーザーに懲役を設定
    - prison_sentences テーブルに記録
    - 該当ユーザーのすべての銀行口座を凍結（status='frozen'）
    """

# ?労働コマンドの処理（懲役中の場合の特別処理）
def do_prison_work(user_id: str) -> dict:
    """
    懲役中ユーザーの?労働
    - ノルマカウント +1
    - ノルマ達成時に remaining_days を -1
    - 稼いだ金は準備預金へ振り込み
    - 釈放日に達したら自動釈放
    """

# 1日1回の分配処理
def distribute_rehabilitation_fund() -> dict:
    """
    1日1回実行（バックグラウンド）
    - 準備預金から全額を回収
    - 懲役中でないユーザーに平等に分配
    """

# ユーザーの懲役ステータス確認
def get_prisoner_status(user_id: str) -> dict:
    """
    懲役中か、残り日数はいくつかを返す
    """

# 釈放処理
def release_prisoner(user_id: str) -> dict:
    """
    懲役終了時に実行
    - prison_sentences レコード削除またはステータス更新
    - 凍結された口座を復活（status='active'）
    """
```

#### B. `commands.py` - 管理者コマンド

管理者ユーザーID: `U87b0fbb89b407cda387dd29329c78259`

```python
def is_admin(user_id: str) -> bool:
    """管理者チェック"""
    return user_id == "U87b0fbb89b407cda387dd29329c78259"

def handle_admin_user_accounts(event, user_id: str, target_user_id: str):
    """?ユーザー口座 [user_id]"""
    # 対象ユーザーの全口座を通帳形式で表示

def handle_admin_account_number(event, user_id: str, account_number: str):
    """?口座番号 [口座番号]"""
    # 口座番号から口座を検索して通帳形式で表示

def handle_admin_sentence(event, user_id: str, target_user_id: str, start_date: str, days: int, quota: int):
    """?懲役 [user_id] [施行日] [日数] [ノルマ]"""
    # 懲役を設定

def handle_admin_freeze_account(event, user_id: str, account_number: str):
    """?凍結 [口座番号]"""
    # 口座を凍結（status='frozen'）
```

---

## 3. ?労働コマンドの修正

### 既存: `apps/work/commands.py`

現在のハンドラー `handle_work_command()` を修正：

```python
def handle_work_command(event, user_id):
    """?労働コマンド"""
    
    # ===== NEW: 懲役中チェック =====
    from apps.prison import prison_service
    prisoner_status = prison_service.get_prisoner_status(user_id)
    if prisoner_status['is_imprisoned']:
        # 懲役中のみ反応
        work_result = prison_service.do_prison_work(user_id)
        # メッセージ表示
        return
    
    # ===== 既存の処理 =====
    # (通常の?労働処理)
```

### Flex メッセージ表示例

懲役中のユーザーが?労働を実行時：
```
【懲役中】
残り懲役日数: 30日
本日のノルマ: 5/5 完了 ✓
→ 本日のノルマを達成しました！残り懲役日数が1短くなりました

稼いだ給与: ¥5,000 → 準備預金へ振り込み
```

---

## 4. 犯罪者更生給付金の配布システム

### 4.1 バックグラウンド スケジューラー

ファイル: `apps/prison/rehabilitation_scheduler.py`

```python
def run_daily_distribution():
    """
    毎日午前9時に実行（例）
    1. prison_rehabilitation_fund から全額を回収
    2. 懲役中でないすべてのユーザーを取得
    3. 金額を平等に分配
    4. 各ユーザーの主要口座へ振込
    5. 分配履歴を記録
    """
```

### 4.2 main.py への統合

```python
from apps.prison.rehabilitation_scheduler import start_rehabilitation_distribution_scheduler

# 起動時に実行
start_rehabilitation_distribution_scheduler()
```

---

## 5. auto_reply.py への統合

### 5.1 コマンドルーティング追加

```python
# === 管理者コマンド（admin_id チェック） ===
if text.startswith("?ユーザー口座 "):
    if not prison_commands.is_admin(user_id):
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text="このコマンドは管理者のみ実行可能です"))
        return
    target_user_id = text.replace("?ユーザー口座 ", "").strip()
    prison_commands.handle_admin_user_accounts(event, user_id, target_user_id)
    return

if text.startswith("?口座番号 "):
    if not prison_commands.is_admin(user_id):
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text="このコマンドは管理者のみ実行可能です"))
        return
    account_number = text.replace("?口座番号 ", "").strip()
    prison_commands.handle_admin_account_number(event, user_id, account_number)
    return

if text.startswith("?懲役 "):
    if not prison_commands.is_admin(user_id):
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text="このコマンドは管理者のみ実行可能です"))
        return
    # パース: "?懲役 [user_id] [start_date] [days] [quota]"
    params = text.replace("?懲役 ", "").split()
    prison_commands.handle_admin_sentence(event, user_id, params[0], params[1], int(params[2]), int(params[3]))
    return

if text.startswith("?凍結 "):
    if not prison_commands.is_admin(user_id):
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text="このコマンドは管理者のみ実行可能です"))
        return
    account_number = text.replace("?凍結 ", "").strip()
    prison_commands.handle_admin_freeze_account(event, user_id, account_number)
    return
```

---

## 6. 実装タスク順序

### フェーズ 1: データベース設定
- [ ] マイグレーションファイル作成 (`migrations/create_prison_system.sql`)
- [ ] テーブル定義確認・実行

### フェーズ 2: 懲役システムのコア実装
- [ ] `apps/prison/prison_models.py` - ORM モデル定義
- [ ] `apps/prison/prison_service.py` - ビジネスロジック実装
- [ ] `apps/prison/prison_flex.py` - メッセージテンプレート

### フェーズ 3: 管理者コマンド実装
- [ ] `apps/prison/commands.py` - 管理者コマンドハンドラー
- [ ] `auto_reply.py` - コマンドルーティング統合

### フェーズ 4: ?労働コマンド修正
- [ ] `apps/work/commands.py` - 懲役中の特別処理追加

### フェーズ 5: 給付金配布システム
- [ ] `apps/prison/rehabilitation_scheduler.py` - スケジューラー実装
- [ ] `main.py` - バックグラウンドタスク統合

### フェーズ 6: テスト・デバッグ
- [ ] 管理者コマンドの動作確認
- [ ] 懲役中のユーザーの?労働実行確認
- [ ] 給付金分配スケジューラーの動作確認

---

## 7. 主要な実装上の注意点

### 7.1 懲役中ユーザーの制限

- **?労働以外のコマンドは反応しない**
  - `auto_reply.py` で懲役ステータスをチェック
  - 懲役中かつ?労働以外のコマンドの場合：「懲役中のため、?労働のみが実行可能です」と返す

### 7.2 準備預金への振り込み

- 既存の `RESERVE_ACCOUNT_NUMBER = '7777777'` を活用
- 懲役中ユーザーの?労働で稼いだ金は、通常口座ではなく準備預金へ

### 7.3 口座凍結の自動管理

- 懲役設定時に対象ユーザーの**全口座を凍結**
- 釈放時に**全口座を復活**

### 7.4 スケジューラーの実装方法

2つの選択肢：
- **オプション A**: APScheduler（定期実行）
- **オプション B**: Cron ジョブ（外部スケジューラー）

現在のシステム（`apps/stock/background_updater.py`）から参考に、APScheduler の使用を推奨。

---

## 8. 実装例（概要）

### 懲役を設定する場合

```
管理者: ?懲役 U98765432abcdef 2025-01-01 30 5
→ user_id=U98765432abcdef に対して
  - 施行日: 2025-01-01
  - 懲役日数: 30日
  - 1日のノルマ: 5回
  を設定
→ 該当ユーザーの全口座を凍結
```

### ノルマ達成パターン

```
懲役中ユーザー: ?労働 （1日5回実行）
1回目: ✓ ¥1,000 → 準備預金へ (ノルマ 1/5)
2回目: ✓ ¥1,000 → 準備預金へ (ノルマ 2/5)
3回目: ✓ ¥1,000 → 準備預金へ (ノルマ 3/5)
4回目: ✓ ¥1,000 → 準備預金へ (ノルマ 4/5)
5回目: ✓ ¥1,000 → 準備預金へ (ノルマ 5/5)
→ 本日のノルマ達成！残り懲役日数が1短くなりました（30日 → 29日）
```

### ノルマ未達成パターン

```
懲役中ユーザー: ?労働 （1日3回だけ実行）
1回目～3回目で終了 (ノルマ 3/5)
→ 本日のノルマ未達成のため、残り懲役日数は減りません
```

---

## 9. 将来的な拡張案

- [ ] 懲役中ユーザーのステータス表示コマンド（`?懲役状況`）
- [ ] 懲役記録のログ表示（管理者用）
- [ ] 早期釈放システム（寛恕制度）
- [ ] 複数犯による連帯懲役機能

---

## 10. 完成イメージ

| 機能 | 実装状況 |
|------|--------|
| 懲役システム | 未実装 |
| 管理者コマンド | 未実装 |
| ?労働修正 | 未実装 |
| 給付金配布 | 未実装 |
| バックグラウンドスケジューラー | 未実装 |

このプランに基づいて、段階的に実装を進めてください。