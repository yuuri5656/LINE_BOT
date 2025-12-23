# 統合ドキュメント — 実装・アーキテクチャ・動作まとめ

このドキュメントはリポジトリ全体の実装、アーキテクチャ、主要な動作フローを一箇所にまとめた参照資料です。

**リポジトリの位置**
- ルート: リポジトリルートに `main.py`, `config.py`, `requirements.txt` がある。
- 主要フォルダ: [core](core), [apps](apps), [document](document), [migrations](migrations)

**目的**
- LINE Bot の会話処理、各種サブシステム（銀行、ショップ、在庫、ゲーム、拘置所など）の調停・実行を行うボット実装。

## 1. 高レベルアーキテクチャ

- エントリポイント: `main.py` — 起動時にLINE webhookサーバやハンドラを初期化する。
- リクエスト処理: [core/handler.py](core/handler.py) が受信イベントを受け取り、セッション管理とコマンドディスパッチを実行。
- セッション管理: [core/sessions.py](core/sessions.py) と各サブシステム内の `session_manager.py` がユーザー状態を管理。
- サブシステム（機能毎）: `apps/` 以下に機能別モジュールが分離されている。
  - `apps/banking`：口座操作、送金、バンクサービス。
  - `apps/stock`：株価更新、チャート、取引ロジック。
  - `apps/games`：ミニゲーム（ブラックジャック、RPS等）。
  - `apps/shop`：仮想商品と購入処理。
  - `apps/prison`：拘置所システムの業務ロジック。

## 2. 主要コンポーネント詳細

- `core/api.py`：外部APIとの共通ラッパやHTTPユーティリティ。
- `core/handler.py`：イベント振り分け、認証、エラーハンドリング。
- `apps/*/commands.py`：ユーザーコマンドの解釈とhigh-level ディスパッチ。
- `apps/*/*_service.py`：ドメインロジック（ビジネスルール）を実装。
- `apps/*/*_flex.py` / `*_flex.py`：LINEのFlex Message テンプレートを定義。
- `migrations/`：SQLマイグレーションスクリプト（データベーススキーマ管理）。

## 3. データフロー（代表例：送金）

1. ユーザーがLINEで送金コマンドを入力。
2. `core/handler.py` がイベント受信 → `apps/banking/commands.py` にルーティング。
3. コマンドは `session_manager` を参照して会話状態を確認。
4. 入力が揃ったら `bank_service.py` の送金処理を呼ぶ。
5. DB更新（トランザクション）後、結果をFlexで整形し返信。

参照ファイル: [apps/banking/transfer_handler.py](apps/banking/transfer_handler.py), [apps/banking/bank_service.py](apps/banking/bank_service.py)

## 4. 実装上の重要な考慮点

- セッション単位でステートを保持し、会話フローを制御する設計。
- 各サブシステムは `service` 層にビジネスロジックを集約し、コマンド層は薄く保つ。
- マイグレーションSQLは `migrations/` に保存。デプロイ時に順次適用する。
- ログは `apps/recording_logs.py` 等で集中的に扱い、問題発生時の調査を容易にしている。

## 5. ローカル起動と依存関係

- 必要要件: `requirements.txt` を参照。
- 環境変数: `config.py` または環境変数からLINEチャネルシークレット等を供給する想定。
- マイグレーション適用: DB の種類に応じて `migrations/` のSQLを流す。
- 起動例（仮）:

```powershell
python main.py
```

## 6. テストとデバッグ

- 単体テスト: 現在専用テストディレクトリは無いが、各 `service` 関数を小さくして単体テストを書きやすくすることを推奨。
- ログ確認: ログ出力を見てステップを追う。Webhook テストはLINE Developer コンソールのWebhook送信機能を利用。

## 7. 追加情報と参照先

- アーキテクチャ補足: [document/ARCHITECTURE.md](document/ARCHITECTURE.md)
- 既存の実装メモ: [document/IMPLEMENTATION_COMPLETE.md](document/IMPLEMENTATION_COMPLETE.md)
- マイグレーション一覧: [migrations](migrations)

## 8. 次の作業候補

- 図（シーケンス図 / コンポーネント図）の追加（PlantUML or Mermaid）。
- 各サブシステムのAPI仕様書（エンドポイント、入力/出力フォーマット）を追加。
- CI用のテストスイート整備。

---
ドキュメントをさらに詳細化（図や個別関数の図示）しますか？要望を教えてください。

## サブシステム個別ドキュメント

- Banking: [document/subsystems/banking.md](document/subsystems/banking.md)
- Stock: [document/subsystems/stock.md](document/subsystems/stock.md)
- Games: [document/subsystems/games.md](document/subsystems/games.md)
- Shop: [document/subsystems/shop.md](document/subsystems/shop.md)
- Prison: [document/subsystems/prison.md](document/subsystems/prison.md)
- Core / Utilities / Rich Menu / Work: [document/subsystems/core_and_utils.md](document/subsystems/core_and_utils.md)

これらの個別ドキュメントは今後さらに拡張して、シーケンス図、主要関数リスト、関連SQL/テーブル定義、サンプルイベント・サンプル出力を追加します。
