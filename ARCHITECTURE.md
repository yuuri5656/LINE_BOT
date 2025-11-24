# アーキテクチャ再構築ドキュメント

## 概要

LINE BOTプロジェクトのアーキテクチャを再構築し、銀行機能とゲーム機能を完全に分離しました。
各機能は独自のディレクトリに配置され、明確な責務を持つようになりました。

## ディレクトリ構造

```
apps/
├── banking/              # 銀行機能（カプセル化済み）
│   ├── __init__.py
│   ├── api.py           # 外部向けAPIファサード（外部はこれのみをimport）
│   ├── bank_service.py  # 内部実装（直接importしない）
│   ├── session_handler.py # 口座開設フロー管理
│   ├── account_creation.py # 口座作成処理
│   ├── main_bank_system.py # ORMモデル定義
│   ├── commands.py      # 銀行コマンドハンドラー
│   └── session_manager.py # 銀行専用セッション管理
│
├── games/               # ゲーム機能
│   ├── __init__.py
│   ├── minigames.py     # ゲームセッション管理
│   ├── rps_game.py      # じゃんけんゲーム
│   ├── commands.py      # ゲームコマンドハンドラー
│   └── session_manager.py # ゲーム専用セッション管理
│
├── utilities/           # ユーティリティ機能
│   ├── __init__.py
│   └── commands.py      # 汎用コマンド（時間割、おみくじ等）
│
├── auto_reply.py        # メッセージルーティング（150行程度に削減）
├── help_flex.py         # ヘルプメッセージ
└── recording_logs.py    # ログ記録

core/
├── api.py              # LINE Messaging API設定
├── handler.py          # イベントハンドラー
└── sessions.py         # 統合セッション管理

minigame/               # 旧ディレクトリ（削除可能だが保持）
└── (旧ファイル群)
```

## アーキテクチャ原則

### 1. カプセル化

#### 銀行機能
- **外部アクセス**: `apps.banking.api` の `banking_api` のみ使用
- **禁止**: `apps.banking.bank_service` への直接import
- **理由**: 内部実装を隠蔽し、変更の影響を局所化

```python
# ✅ 正しい使い方
from apps.banking.api import banking_api
account = banking_api.get_account_by_user(user_id)

# ❌ 間違った使い方
from apps.banking import bank_service  # 直接importは禁止
```

#### ゲーム機能
- **外部アクセス**: `apps.games.commands` のハンドラー関数を使用
- **内部**: `apps.games.minigames` のセッション管理は内部実装

### 2. コマンドパターン

`auto_reply.py` はルーティングのみを担当し、実際の処理は各コマンドハンドラーに委譲：

- `apps.banking.commands`: 口座開設、口座情報等
- `apps.games.commands`: じゃんけん、参加、開始等
- `apps.utilities.commands`: 時間割、おみくじ、RPN等

### 3. セッション管理の分離

#### 統合セッションマネージャー (`core.sessions`)
- 後方互換性を保ちつつ、各機能のセッションマネージャーへアクセスを提供
- `sessions.banking`: 銀行セッション
- `sessions.game`: ゲームセッション

#### 機能別セッションマネージャー
- `apps.banking.session_manager.BankingSessionManager`: 口座開設フロー
- `apps.games.session_manager.GameSessionManager`: ゲーム参加状態
- `apps.games.minigames.GroupManager`: グループゲームセッション

### 4. 依存性の方向

```
auto_reply.py
    ↓
commands.py (banking/games/utilities)
    ↓
api.py (banking) / minigames.py (games)
    ↓
bank_service.py / main_bank_system.py
```

- 上位層は下位層に依存
- 下位層は上位層を知らない
- 循環依存なし

## API利用例

### 銀行機能

```python
from apps.banking.api import banking_api

# 口座作成
account = banking_api.create_account(event, account_info, sessions)

# 口座情報取得
accounts = banking_api.get_accounts_by_user(user_id)

# 入出金
banking_api.withdraw_from_user(user_id, 100, 'JPY')
banking_api.deposit_to_user(user_id, 200, 'JPY')

# ミニゲーム口座
result = banking_api.register_minigame_account(user_id, full_name, branch_code, account_number, pin)
minigame_info = banking_api.get_minigame_account_info(user_id)
```

### ゲーム機能

```python
from apps.games.commands import (
    handle_janken_start,
    handle_join_game,
    handle_game_start
)

# ゲーム開始
handle_janken_start(event, user_id, text, display_name, group_id, sessions)

# 参加
handle_join_game(event, user_id, display_name, group_id)

# 開始
handle_game_start(event, user_id, group_id)
```

## 主要な変更点

### Before (旧構造)

```python
# auto_reply.py (470行)
from apps.minigame.minigames import ...
from apps.minigame.bank_reception import ...
from apps.minigame import bank_service

# グローバルsessions辞書を共有
def auto_reply(event, text, user_id, group_id, display_name, sessions):
    # 銀行、ゲーム、ユーティリティのロジックが混在
    if text == "?口座開設":
        bank_reception(...)
    if text == "?じゃんけん":
        play_rps_game(...)
    # ...470行続く
```

### After (新構造)

```python
# auto_reply.py (150行程度)
from apps.banking import commands as banking_commands
from apps.games import commands as game_commands
from apps.utilities import commands as utility_commands

def auto_reply(event, text, user_id, group_id, display_name, sessions):
    # ルーティングのみ
    if text == "?口座開設":
        banking_commands.handle_account_opening(...)
    if text == "?じゃんけん":
        game_commands.handle_janken_start(...)
    # ...シンプルな振り分けのみ
```

## 循環import回避策

### 遅延インポート

```python
def _get_bank_service():
    """遅延インポートでbank_serviceを取得（循環import回避）"""
    from apps.banking import bank_service
    return bank_service
```

### プロパティでのインポート

```python
@property
def banking(self):
    """銀行セッションマネージャーを取得"""
    if self._banking_manager is None:
        from apps.banking.session_manager import banking_session_manager
        self._banking_manager = banking_session_manager
    return self._banking_manager
```

## テストガイド

### 口座開設テスト
1. 塩爺との個別チャットで `?口座開設` を入力
2. フルネーム入力
3. 生年月日入力
4. 支店選択
5. 口座種別選択
6. 暗証番号設定
7. 完了メッセージを確認

### ミニゲーム口座登録テスト
1. 個別チャットで `?ミニゲーム口座登録` を入力
2. 支店番号、口座番号、氏名、暗証番号を順に入力
3. 登録完了メッセージを確認

### じゃんけんテスト
1. グループチャットで `?じゃんけん` を入力
2. 他のユーザーが `?参加` を入力
3. ホストが `?開始` を入力
4. 個別チャットで手（グー/チョキ/パー）を送信
5. 結果FlexMessageを確認

### 口座情報表示テスト
1. 個別チャットで `?口座情報` を入力
2. カルーセル形式で口座情報が表示されることを確認

## トラブルシューティング

### import エラーが出る場合
- `apps.minigame` からのimportが残っていないか確認
- `apps.banking.api` を使用しているか確認

### セッションが保持されない
- `core.sessions.sessions` を使用しているか確認
- 銀行セッションは `sessions.banking` で管理されている

### ゲームが開始できない
- `apps.games.minigames.manager` が正しく初期化されているか確認
- グループIDが正しく渡されているか確認

## 今後の拡張

### 新機能追加手順

1. **新しい機能ディレクトリを作成**: `apps/新機能名/`
2. **APIファサードを実装**: `apps/新機能名/api.py`
3. **コマンドハンドラーを作成**: `apps/新機能名/commands.py`
4. **セッションマネージャーを実装**: `apps/新機能名/session_manager.py`
5. **auto_reply.py にルーティングを追加**

### テスト追加
- 各機能ごとにユニットテストを作成
- `tests/test_banking_api.py`
- `tests/test_game_commands.py`

## まとめ

この再構築により：

✅ **明確な責務分離**: 銀行、ゲーム、ユーティリティが独立
✅ **カプセル化**: 外部からの直接アクセスを禁止
✅ **保守性向上**: 変更の影響範囲が限定的
✅ **拡張性**: 新機能の追加が容易
✅ **テスト容易性**: 各機能を独立してテスト可能

470行の巨大な`auto_reply.py`が150行のシンプルなルーターに変わり、
各機能の実装は独立したモジュールに分離されました。
