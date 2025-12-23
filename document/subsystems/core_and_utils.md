# サブシステム: Core / Utilities / Rich Menu / Work

## 概要
このドキュメントは `core` と共通ユーティリティ、`apps/rich_menu`, `apps/work` の要点をまとめます。

## `core`
- 主要責務: Webhook受信、イベントのルーティング、セッション管理。
- 主要ファイル: `core/handler.py`, `core/api.py`, `core/sessions.py`。
- 注意点: ここがボットの入口となるため例外処理と認証が重要。

## `apps/rich_menu`
- 主要責務: リッチメニュー管理、テンプレート配置、メニュー更新。
- 主要ファイル: `apps/rich_menu/menu_manager.py`, `menu_templates.py`。

## `apps/work`
- 主要責務: 作業システム、報酬、出勤管理。
- 主要ファイル: `apps/work/work_service.py`, `work_flex.py`。

## 共通ユーティリティ
- `apps/utilities` 以下に汎用的な関数、タイムゾーンユーティリティなどがある。共通処理はここに集約し再利用する。

## 参照
- `core`/`apps` ディレクトリを参照して、必要な関数・クラスの詳細を個別で抽出してください。

## 主要関数 / クラス（抜粋）
- `UnifiedSessionManager` (`core/sessions.py`)
- `on_message(event)` (`core/handler.py`)
- `on_postback(event)` (`core/handler.py`)
- `show_loading_animation(chat_id: str, loading_seconds: int = 5)` (`core/api.py`)
- `menu_manager.py` のリッチメニュー更新関数群

（各ファイルからさらに細かい関数一覧を抽出して追加できます）
