# サブシステム: Stock（株式）

## 概要
`apps/stock` は株価データの取得・更新、ユーザーの保有株管理、売買ロジック、チャート生成を担当します。

## 主要責務
- 定期的な株価取得（バッチ/バックグラウンドジョブ）
- ユーザーの買付・売却処理
- チャート生成と表示用データ整形

## 主要ファイル
- `apps/stock/background_updater.py` — 価格更新ジョブ
- `apps/stock/price_service.py` — 価格取得/加工ロジック
- `apps/stock/stock_service.py` — 売買ロジック、残高/保有計算
- `apps/stock/chart_service.py` — チャート生成

## データフロー（価格更新の例）
1. `background_updater` が外部APIを呼び `price_service` で正規化
2. DBに保存して、`stock_service` でポートフォリオ評価を更新
3. 変化があれば通知やランキング更新を実行

## マイグレーション / テーブル
- 株式価格テーブル、保有テーブル、トランザクションテーブルを想定。`migrations/` を参照。

## 注意点
- 外部APIのレート制限とフォールバック
- 時刻（タイムゾーン）と市場の取引時間の考慮

## 参照
- 関連コード: [apps/stock](../../apps/stock)

## 主要関数 / クラス
- `class StockSymbol`
- `class StockPriceHistory`
- `class StockAccount`
- `class UserStockHolding`
- `class StockTransaction`
- `class AITrader`
- `class AITraderHolding`
- `class AITraderTransaction`
- `class StockEvent`
- `class DividendPayment`
- `get_stock_db()`

