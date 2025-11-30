"""
チャート生成サービス - matplotlib による株価チャート画像生成

外部から直接インポートせず、api.py経由で使用すること
"""
import matplotlib
matplotlib.use('Agg')  # GUIバックエンドを使わない
import matplotlib.pyplot as plt
import japanize_matplotlib
from typing import List, Dict, Optional
import io
import base64
from datetime import datetime
from .price_service import price_service


class ChartService:
    """株価チャート生成サービス"""

    @staticmethod
    def generate_stock_chart(symbol_code: str, days: int = 30) -> Optional[str]:
        """
        株価チャートを生成してBase64エンコードした画像を返す

        Args:
            symbol_code: 銘柄コード
            days: 表示日数

        Returns:
            Base64エンコードされた画像データ、失敗時はNone
        """
        try:
            # 株価履歴取得
            history = price_service.get_price_history(symbol_code, limit=days)
            if not history or len(history) < 2:
                return None

            # データ準備
            timestamps = [h['timestamp'] for h in history]
            prices = [h['price'] for h in history]

            # グラフ作成
            fig, ax = plt.subplots(figsize=(10, 6))

            # 折れ線グラフ
            ax.plot(timestamps, prices, linewidth=2, color='#2196F3', marker='o', markersize=4)

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
            buf.close()

            return image_base64

        except Exception as e:
            print(f"チャート生成エラー: {e}")
            return None

    @staticmethod
    def generate_portfolio_chart(holdings: List[Dict]) -> Optional[str]:
        """
        ポートフォリオ（保有株の割合）チャートを生成

        Args:
            holdings: 保有株リスト

        Returns:
            Base64エンコードされた画像データ
        """
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
            buf.close()

            return image_base64

        except Exception as e:
            print(f"ポートフォリオチャート生成エラー: {e}")
            return None

    @staticmethod
    def generate_comparison_chart(holdings: List[Dict]) -> Optional[str]:
        """
        保有株の損益比較チャート（棒グラフ）を生成

        Args:
            holdings: 保有株リスト

        Returns:
            Base64エンコードされた画像データ
        """
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
            buf.close()

            return image_base64

        except Exception as e:
            print(f"損益比較チャート生成エラー: {e}")
            return None


# サービスインスタンス
chart_service = ChartService()
