"""
株価バックグラウンド更新システム

定期的に株価を更新し、AIトレーダーの取引を実行する
"""
import threading
import time
from datetime import datetime, time as dt_time
from apps.stock.api import stock_api
from apps.utilities.timezone_utils import now_jst


class StockBackgroundUpdater:
    """株価バックグラウンド更新"""

    def __init__(self, ai_trade_interval: int = 120, price_update_interval: int = 300):
        """
        Args:
            ai_trade_interval: AI取引の間隔（秒）デフォルトは120秒（2分）
            price_update_interval: 株価更新の間隔（秒）デフォルトは300秒（5分）
        """
        self.ai_trade_interval = ai_trade_interval
        self.price_update_interval = price_update_interval
        self.running = False
        self.thread = None
        self.last_dividend_date = None  # 最後に配当金を支払った日付
        # 起動時に現在時刻を設定することで、即座に実行されるのを防ぐ
        self.last_ai_trade_time = time.time()  # 最後にAI取引を実行した時刻
        self.last_price_update_time = time.time()  # 最後に株価更新を実行した時刻
        self._lock = threading.Lock()  # スレッド起動の排他制御

    def start(self):
        """バックグラウンド更新を開始"""
        with self._lock:
            # 既存スレッドが生きている場合はスキップ
            if self.thread is not None and self.thread.is_alive():
                print("[株価更新] 既に実行中です（スレッド生存確認済み）")
                return

            # 既存スレッドをクリーンアップ
            if self.thread is not None:
                print("[株価更新] 古いスレッドを検出、クリーンアップします")
                self.running = False
                self.thread = None

            self.running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()
            print(f"[株価更新] バックグラウンド更新を開始しました（AI取引: {self.ai_trade_interval}秒, 株価更新: {self.price_update_interval}秒）")

    def stop(self):
        """バックグラウンド更新を停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[株価更新] バックグラウンド更新を停止しました")

    def _update_loop(self):
        """更新ループ（最小間隔30秒でチェック）"""
        check_interval = 30  # 30秒ごとにチェック

        while self.running:
            try:
                current_time = time.time()
                now = now_jst()

                # AI取引の実行判定（2分ごと）
                if current_time - self.last_ai_trade_time >= self.ai_trade_interval:
                    try:
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] AI取引開始")
                        stock_api.execute_ai_trading()
                        self.last_ai_trade_time = current_time
                    except Exception as ai_error:
                        import traceback
                        print(f"[AI取引エラー] {ai_error}")
                        print(f"エラー詳細:\n{traceback.format_exc()}")
                        # エラーでも次回実行できるように時刻を更新
                        self.last_ai_trade_time = current_time

                # 株価更新の実行判定（5分ごと）
                if current_time - self.last_price_update_time >= self.price_update_interval:
                    try:
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 株価更新開始")
                        stock_api.update_all_prices()
                        self.last_price_update_time = current_time
                        print(f"[株価更新] 更新完了")
                    except Exception as price_error:
                        import traceback
                        print(f"[株価更新エラー] {price_error}")
                        print(f"エラー詳細:\n{traceback.format_exc()}")
                        # エラーでも次回実行できるように時刻を更新
                        self.last_price_update_time = current_time

                # 配当金支払い（1日1回、午前8時前後）
                current_date = now.date()
                current_hour = now.hour

                # 午前7時〜9時の間で、まだ今日支払っていない場合
                if 7 <= current_hour < 9 and self.last_dividend_date != current_date:
                    try:
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 配当金支払い開始")
                        stock_api.pay_dividends()
                        self.last_dividend_date = current_date
                    except Exception as dividend_error:
                        import traceback
                        print(f"[配当金支払いエラー] {dividend_error}")
                        print(f"エラー詳細:\n{traceback.format_exc()}")
                        # エラーでも今日の処理は完了扱いにする
                        self.last_dividend_date = current_date

                # 次のチェックまで待機
                time.sleep(check_interval)

            except Exception as e:
                import traceback
                print(f"[株価更新] 予期しないエラーが発生しました: {e}")
                print(f"エラー詳細:\n{traceback.format_exc()}")
                # エラーが発生しても継続
                time.sleep(check_interval)

    def force_update(self):
        """即座に更新を実行（手動トリガー用）"""
        print("[株価更新] 手動更新を実行します")
        try:
            stock_api.execute_ai_trading()
            stock_api.update_all_prices()
            print("[株価更新] 手動更新完了")
        except Exception as e:
            print(f"[株価更新] 手動更新エラー: {e}")


# グローバルインスタンス（AI取引: 2分, 株価更新: 5分）
background_updater = StockBackgroundUpdater(ai_trade_interval=120, price_update_interval=300)


def start_background_updater():
    """バックグラウンド更新を開始する関数"""
    background_updater.start()


def stop_background_updater():
    """バックグラウンド更新を停止する関数"""
    background_updater.stop()


def force_update():
    """手動で更新を実行する関数"""
    background_updater.force_update()


if __name__ == "__main__":
    # テスト実行
    print("株価バックグラウンド更新システムのテスト")
    start_background_updater()

    try:
        # 5分間実行
        print("5分間実行します... (Ctrl+Cで終了)")
        time.sleep(300)
    except KeyboardInterrupt:
        print("\n終了します")
    finally:
        stop_background_updater()
