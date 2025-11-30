"""
株価バックグラウンド更新システム

定期的に株価を更新し、AIトレーダーの取引を実行する
"""
import threading
import time
from datetime import datetime, time as dt_time
from apps.stock.api import stock_api


class StockBackgroundUpdater:
    """株価バックグラウンド更新"""

    def __init__(self, update_interval: int = 60):
        """
        Args:
            update_interval: 更新間隔（秒）デフォルトは60秒
        """
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.last_dividend_date = None  # 最後に配当金を支払った日付

    def start(self):
        """バックグラウンド更新を開始"""
        if self.running:
            print("[株価更新] 既に実行中です")
            return

        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        print(f"[株価更新] バックグラウンド更新を開始しました（間隔: {self.update_interval}秒）")

    def stop(self):
        """バックグラウンド更新を停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[株価更新] バックグラウンド更新を停止しました")

    def _update_loop(self):
        """更新ループ"""
        while self.running:
            try:
                start_time = time.time()
                now = datetime.now()

                # AIトレーダーの取引を実行
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] AI取引開始")
                stock_api.execute_ai_trading()

                # 株価更新
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 株価更新開始")
                stock_api.update_all_prices()

                # 配当金支払い（1日1回、午前8時前後）
                current_date = now.date()
                current_hour = now.hour

                # 午前7時〜9時の間で、まだ今日支払っていない場合
                if 7 <= current_hour < 9 and self.last_dividend_date != current_date:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 配当金支払い開始")
                    stock_api.pay_dividends()
                    self.last_dividend_date = current_date

                elapsed_time = time.time() - start_time
                print(f"[株価更新] 更新完了（処理時間: {elapsed_time:.2f}秒）")

                # 次の更新まで待機
                sleep_time = max(0, self.update_interval - elapsed_time)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"[株価更新] エラーが発生しました: {e}")
                # エラーが発生しても継続
                time.sleep(self.update_interval)

    def force_update(self):
        """即座に更新を実行（手動トリガー用）"""
        print("[株価更新] 手動更新を実行します")
        try:
            stock_api.execute_ai_trading()
            stock_api.update_all_prices()
            print("[株価更新] 手動更新完了")
        except Exception as e:
            print(f"[株価更新] 手動更新エラー: {e}")


# グローバルインスタンス
background_updater = StockBackgroundUpdater(update_interval=60)


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
