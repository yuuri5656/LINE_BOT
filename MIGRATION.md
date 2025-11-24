# マイグレーションガイド

## 変更されたファイルの対応表

### 移動したファイル

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `apps/minigame/bank_service.py` | `apps/banking/bank_service.py` | 銀行サービス実装（直接importしない） |
| `apps/minigame/bank_reception.py` | `apps/banking/session_handler.py` | 口座開設フロー管理 |
| `apps/minigame/account_creation.py` | `apps/banking/account_creation.py` | 口座作成処理 |
| `apps/minigame/main_bank_system.py` | `apps/banking/main_bank_system.py` | ORMモデル定義 |
| `apps/minigame/minigames.py` | `apps/games/minigames.py` | ゲームセッション管理 |
| `apps/minigame/rps_game.py` | `apps/games/rps_game.py` | じゃんけんゲーム |

### 新規作成したファイル

| ファイルパス | 説明 |
|-------------|------|
| `apps/banking/__init__.py` | 銀行パッケージ |
| `apps/banking/api.py` | **銀行APIファサード（外部はこれのみをimport）** |
| `apps/banking/commands.py` | 銀行コマンドハンドラー |
| `apps/banking/session_manager.py` | 銀行専用セッション管理 |
| `apps/games/__init__.py` | ゲームパッケージ |
| `apps/games/commands.py` | ゲームコマンドハンドラー |
| `apps/games/session_manager.py` | ゲーム専用セッション管理 |
| `apps/utilities/__init__.py` | ユーティリティパッケージ |
| `apps/utilities/commands.py` | 汎用コマンドハンドラー |
| `ARCHITECTURE.md` | アーキテクチャドキュメント |

### 大幅に変更したファイル

| ファイルパス | 変更内容 |
|-------------|---------|
| `apps/auto_reply.py` | 470行→150行に削減。ルーティングのみに特化 |
| `core/sessions.py` | 統合セッションマネージャーを実装 |

## import文の変更例

### 銀行機能

```python
# Before
from apps.minigame import bank_service
account = bank_service.get_account_info_by_user(user_id)
bank_service.withdraw_from_user(user_id, 100, 'JPY')

# After
from apps.banking.api import banking_api
account = banking_api.get_account_by_user(user_id)
banking_api.withdraw_from_user(user_id, 100, 'JPY')
```

### ゲーム機能

```python
# Before
from apps.minigame.minigames import manager, join_game_session
from apps.minigame.rps_game import play_rps_game

# After
from apps.games.minigames import manager, join_game_session
from apps.games.rps_game import play_rps_game
# または
from apps.games.commands import handle_janken_start, handle_join_game
```

### セッション管理

```python
# Before
from core.sessions import sessions
sessions[user_id] = {"step": 1}  # 直接辞書操作

# After
from core.sessions import sessions
sessions[user_id] = {"step": 1}  # 後方互換性あり（内部的にbanking.session_managerを使用）

# 新しい推奨方法
sessions.banking.set(user_id, {"step": 1})
```

## 動作確認手順

### 1. 構文エラーチェック

```powershell
python -m py_compile main.py
python -m py_compile apps/auto_reply.py
python -m py_compile apps/banking/api.py
python -m py_compile apps/games/commands.py
```

全てエラーなく完了すること。

### 2. アプリケーション起動

```powershell
python main.py
```

または

```powershell
flask run
```

エラーなく起動すること。

### 3. 機能テスト

#### 口座開設
1. 塩爺との個別チャットで `?口座開設`
2. 全ステップを完了
3. 「口座の開設が完了しました」メッセージを確認

#### 口座情報表示
1. 個別チャットで `?口座情報`
2. カルーセル形式で口座情報が表示されることを確認

#### ミニゲーム口座登録
1. 個別チャットで `?ミニゲーム口座登録`
2. 支店番号、口座番号、氏名、暗証番号を入力
3. 登録完了メッセージを確認

#### じゃんけんゲーム
1. グループチャットで `?じゃんけん`
2. 別のユーザーが `?参加`
3. ホストが `?開始`
4. 個別チャットで手（グー/チョキ/パー）を送信
5. 結果FlexMessageを確認

#### ヘルプ
1. `?ヘルプ` または `?help`
2. FlexMessage形式のヘルプが表示されることを確認

#### その他のコマンド
- `?userid` - ユーザーID表示
- `?明日の時間割` - 時間割表示
- `?おみくじ` - おみくじ
- `?RPN 3 4 +` - RPN計算機

## ロールバック手順（問題が発生した場合）

```powershell
# 古いauto_reply.pyを復元
Move-Item apps/auto_reply.py apps/auto_reply_new_backup.py -Force
Move-Item apps/auto_reply_old.py apps/auto_reply.py -Force

# 古いminigameディレクトリのファイルを使用するようにimportを変更
# （手動で各ファイルのimport文を修正）
```

## よくある問題と解決策

### ImportError: No module named 'apps.banking'

**原因**: Pythonパスが正しく設定されていない

**解決策**:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### AttributeError: module 'apps.banking.api' has no attribute 'banking_api'

**原因**: 循環importまたはキャッシュの問題

**解決策**:
```powershell
# __pycache__を削除
Remove-Item -Recurse -Force apps/__pycache__
Remove-Item -Recurse -Force apps/banking/__pycache__
Remove-Item -Recurse -Force apps/games/__pycache__
```

### ModuleNotFoundError: No module named 'apps.minigame'

**原因**: 古いimport文が残っている

**解決策**:
```powershell
# 古いimportを検索
grep -r "from apps.minigame" apps/
# 該当箇所を新しいimportに置き換え
```

### セッションが保持されない

**原因**: セッション管理の変更に対応していない

**解決策**:
`core.sessions.sessions` を使用しているか確認。
直接 `sessions` 辞書を操作している箇所は後方互換性があるため、
そのまま動作するはず。

## 今後の開発で注意すること

### 1. 銀行機能を使う場合

```python
# ✅ 必ずapiを経由
from apps.banking.api import banking_api

# ❌ 直接bank_serviceをimportしない
from apps.banking import bank_service  # 禁止
```

### 2. 新しい機能を追加する場合

1. `apps/新機能名/` ディレクトリを作成
2. `api.py` または `commands.py` を実装
3. `auto_reply.py` にルーティングを追加
4. 必要に応じて `session_manager.py` を作成

### 3. セッション管理

```python
# 銀行セッション
from core.sessions import sessions
sessions.banking.set(user_id, data)
data = sessions.banking.get(user_id)

# ゲームセッション（グループ）
from apps.games.minigames import manager
session = manager.get_session(group_id)
```

## チェックリスト

実装完了後、以下を確認してください：

- [ ] 全ての構文チェックがパス
- [ ] アプリケーションが起動する
- [ ] 口座開設が正常に動作
- [ ] 口座情報表示が正常に動作
- [ ] ミニゲーム口座登録が正常に動作
- [ ] じゃんけんゲームが正常に動作
- [ ] ヘルプコマンドが正常に動作
- [ ] その他のコマンドが正常に動作
- [ ] `from apps.minigame` のimportが残っていない（auto_reply_old.py以外）
- [ ] エラーログに異常がない

## サポート

問題が発生した場合は、以下の情報を収集してください：

1. エラーメッセージの全文
2. 実行したコマンド
3. 関連するファイルのimport文
4. スタックトレース

これらの情報があれば、迅速にサポートできます。
