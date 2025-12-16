"""
チャート生成サービス - matplotlib による株価チャート画像生成

外部から直接インポートせず、api.py経由で使用すること
"""
try:
    import matplotlib
    matplotlib.use('Agg')  # GUIバックエンドを使わない
    import matplotlib.pyplot as plt
    import japanize_matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    print(f"[警告] matplotlib/japanize-matplotlibがインストールされていません: {e}")
    MATPLOTLIB_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print(f"[警告] requestsがインストールされていません")
    REQUESTS_AVAILABLE = False

from typing import List, Dict, Optional
import io
import base64
import time
import random
from datetime import datetime
from .price_service import price_service
from config import IMGUR_CLIENT_ID, IMGBB_API_KEY


class ChartService:
    """株価チャート生成サービス"""

    @staticmethod
    def upload_to_imgbb(image_base64: str) -> Optional[str]:
        """
        Base64画像をImgBBにアップロードしてURLを取得

        Args:
            image_base64: Base64エンコードされた画像データ

        Returns:
            アップロードされた画像のURL、失敗時はNone
        """
        if not REQUESTS_AVAILABLE:
            print("[ImgBB] requestsライブラリが利用できません")
            return None

        if not IMGBB_API_KEY:
            print("[ImgBB] IMGBB_API_KEYが設定されていません")
            return None

        # リトライ用設定
        max_retries = 3
        backoff_base = 1

        for attempt in range(1, max_retries + 1):
            try:
                data = {
                    'key': IMGBB_API_KEY,
                    'image': image_base64,
                    # 自動削除（秒）: 5分 = 300秒
                    'expiration': 300
                }

                response = requests.post(
                    'https://api.imgbb.com/1/upload',
                    data=data,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        image_url = result['data']['url']
                        print(f"[ImgBB] 画像アップロード成功: {image_url}")
                        return image_url
                    else:
                        print(f"[ImgBB] アップロード失敗: {result}")
                        return None
                else:
                    # レート制限の判定
                    is_rate_limited = False
                    try:
                        result = response.json()
                    except Exception:
                        result = None

                    if response.status_code == 429:
                        is_rate_limited = True
                    elif result and isinstance(result, dict):
                        err = result.get('error')
                        if isinstance(err, dict):
                            if err.get('code') == 100:
                                is_rate_limited = True
                            elif isinstance(err.get('message'), str) and 'rate' in err.get('message').lower():
                                is_rate_limited = True
                        elif isinstance(err, str) and 'rate' in err.lower():
                            is_rate_limited = True

                    if is_rate_limited and attempt < max_retries:
                        wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                        print(f"[ImgBB] レート制限検出({response.status_code})。{wait:.1f}s後にリトライします ({attempt}/{max_retries})")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"[ImgBB] HTTPエラー: {response.status_code} - {response.text}")
                        return None

            except Exception as e:
                if attempt < max_retries:
                    wait = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    print(f"[ImgBB] アップロードエラー: {e}。{wait:.1f}s後にリトライします ({attempt}/{max_retries})")
                    time.sleep(wait)
                    continue
                print(f"[ImgBB] アップロードエラー: {e}")
                return None

    @staticmethod
    def upload_to_imgur(image_base64: str) -> Optional[str]:
        """
        Base64画像をImgurにアップロードしてURLを取得

        Args:
            image_base64: Base64エンコードされた画像データ

        Returns:
            アップロードされた画像のURL、失敗時はNone
        """
        if not REQUESTS_AVAILABLE:
            print("[Imgur] requestsライブラリが利用できません")
            return None

        if not IMGUR_CLIENT_ID:
            print("[Imgur] IMGUR_CLIENT_IDが設定されていません")
            return None

        try:
            headers = {
                'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'
            }
            data = {
                'image': image_base64,
                'type': 'base64'
            }

            response = requests.post(
                'https://api.imgur.com/3/image',
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['data']['link']
                    print(f"[Imgur] 画像アップロード成功: {image_url}")
                    return image_url
                else:
                    print(f"[Imgur] アップロード失敗: {result}")
                    return None
            else:
                print(f"[Imgur] HTTPエラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"[Imgur] アップロードエラー: {e}")
            return None

    @staticmethod
    def upload_image(image_base64: str) -> Optional[str]:
        """
        Base64画像を画像ホスティングサービスにアップロード
        ImgBB → Imgurの優先順位で試行

        Args:
            image_base64: Base64エンコードされた画像データ

        Returns:
            アップロードされた画像のURL、失敗時はNone
        """
        # ImgBBを優先的に使用（登録が簡単なため）
        if IMGBB_API_KEY:
            url = ChartService.upload_to_imgbb(image_base64)
            if url:
                return url
            print("[画像アップロード] ImgBBが失敗、Imgurを試行...")

        # Imgurをフォールバック
        if IMGUR_CLIENT_ID:
            url = ChartService.upload_to_imgur(image_base64)
            if url:
                return url

        print("[画像アップロード] すべてのサービスが利用できません")
        return None

    @staticmethod
    def generate_stock_chart(symbol_code: str, days: int = 30) -> Optional[str]:
        """
        株価チャートを生成してImgurにアップロード

        Args:
            symbol_code: 銘柄コード
            days: 表示日数

        Returns:
            Imgur画像URL、失敗時はNone
        """
        if not MATPLOTLIB_AVAILABLE:
            print("[チャート] matplotlibが利用できないため、チャート生成をスキップします")
            return None

        try:
            # 株価履歴取得
            history = price_service.get_price_history(symbol_code, limit=days)
            if not history or len(history) < 2:
                return None

            # データ間引き（400ポイント以下に削減）
            max_points = 400
            if len(history) > max_points:
                step = len(history) // max_points
                history = history[::step]  # step間隔でデータを間引く

            # データ準備
            timestamps = [h['timestamp'] for h in history]
            prices = [h['price'] for h in history]

            # グラフ作成
            fig, ax = plt.subplots(figsize=(10, 6))

            # 折れ線グラフ（マーカーは削減してパフォーマンス向上）
            marker_size = 0 if len(timestamps) > 100 else 4
            ax.plot(timestamps, prices, linewidth=2, color='#2196F3', marker='o' if marker_size > 0 else None, markersize=marker_size)

            # グリッド
            ax.grid(True, alpha=0.3, linestyle='--')

            # ラベル
            ax.set_xlabel('日時', fontsize=12)
            ax.set_ylabel('株価 (円)', fontsize=12)
            ax.set_title(f'{symbol_code} 株価推移', fontsize=14, fontweight='bold')

            # X軸の日付フォーマット
            plt.xticks(rotation=45)
            fig.autofmt_xdate()

            # Y軸のフォーマット（カンマ区切り）
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{int(x):,}'))

            # レイアウト調整
            plt.tight_layout()

            # 画像をバイトストリームに保存
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)

            # Base64エンコード
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            # クリーンアップ
            plt.close(fig)
            plt.close('all')  # 念のため全figureをクローズ
            buf.close()

            # 画像アップロード（ImgBBまたはImgur）
            image_url = ChartService.upload_image(image_base64)
            return image_url

        except Exception as e:
            print(f"チャート生成エラー: {e}")
            plt.close('all')  # エラー時もクリーンアップ
            return None

    @staticmethod
    def generate_portfolio_chart(holdings: List[Dict]) -> Optional[str]:
        """
        ポートフォリオ（保有株の割合）チャートを生成してImgurにアップロード

        Args:
            holdings: 保有株リスト

        Returns:
            Imgur画像URL、失敗時はNone
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            if not holdings:
                return None

            # データ準備
            labels = [f"{h['symbol_code']}\n{h['name']}" for h in holdings]
            values = [h['current_value'] for h in holdings]
            colors = plt.cm.Set3(range(len(holdings)))

            # 円グラフ作成
            fig, ax = plt.subplots(figsize=(10, 8))

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 10}
            )

            # パーセント表示のフォントサイズ調整
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)

            ax.set_title('ポートフォリオ構成', fontsize=14, fontweight='bold', pad=20)

            # 画像をバイトストリームに保存
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)

            # Base64エンコード
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            # クリーンアップ
            plt.close(fig)
            plt.close('all')  # 念のため全figureをクローズ
            buf.close()

            # 画像アップロード（ImgBBまたはImgur）
            image_url = ChartService.upload_image(image_base64)
            return image_url

        except Exception as e:
            print(f"ポートフォリオチャート生成エラー: {e}")
            plt.close('all')  # エラー時もクリーンアップ
            return None

    @staticmethod
    def generate_comparison_chart(holdings: List[Dict]) -> Optional[str]:
        """
        保有株の損益比較チャート（棒グラフ）を生成してImgurにアップロード

        Args:
            holdings: 保有株リスト

        Returns:
            Imgur画像URL、失敗時はNone
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            if not holdings:
                return None

            # データ準備
            labels = [h['symbol_code'] for h in holdings]
            profit_loss = [h['profit_loss'] for h in holdings]
            colors = ['#4CAF50' if pl >= 0 else '#F44336' for pl in profit_loss]

            # 棒グラフ作成
            fig, ax = plt.subplots(figsize=(10, 6))

            bars = ax.bar(labels, profit_loss, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

            # 0のラインを強調
            ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

            # グリッド
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')

            # ラベル
            ax.set_xlabel('銘柄コード', fontsize=12)
            ax.set_ylabel('損益 (円)', fontsize=12)
            ax.set_title('保有株 損益状況', fontsize=14, fontweight='bold')

            # Y軸のフォーマット
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{int(x):,}'))

            # 棒の上に数値表示
            for bar, pl in zip(bars, profit_loss):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'¥{int(pl):,}',
                    ha='center',
                    va='bottom' if pl >= 0 else 'top',
                    fontsize=9,
                    fontweight='bold'
                )

            # レイアウト調整
            plt.tight_layout()

            # 画像をバイトストリームに保存
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)

            # Base64エンコード
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            # クリーンアップ
            plt.close(fig)
            plt.close('all')  # 念のため全figureをクローズ
            buf.close()

            # 画像アップロード（ImgBBまたはImgur）
            image_url = ChartService.upload_image(image_base64)
            return image_url

        except Exception as e:
            print(f"損益比較チャート生成エラー: {e}")
            plt.close('all')  # エラー時もクリーンアップ
            return None


# サービスインスタンス
chart_service = ChartService()
