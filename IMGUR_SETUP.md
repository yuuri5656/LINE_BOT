# Imgur API セットアップガイド

株式トレードシステムのチャート機能を有効化するために、Imgur API の設定が必要です。

## 1. 画像アップロード API の設定

**重要**: Imgur は 2024 年以降、新規 API 登録が困難になっています。**ImgBB の使用を強く推奨します**。

### 方法 A: ImgBB（推奨・最も簡単）

1. [ImgBB](https://imgbb.com/)にアクセス
2. 右上の「Sign up」をクリック
   - Google アカウントで即座に登録可能
   - またはメールアドレスで登録
3. ログイン後、[API 設定ページ](https://api.imgbb.com/)にアクセス
4. 「Get API key」ボタンをクリック
5. **API Key**が表示される（例: `1234567890abcdef1234567890abcdef`）
6. コピーして保存

**ImgBB の利点**:

- ✅ 登録が超簡単（1 分で完了）
- ✅ 完全無料、アップロード無制限
- ✅ API アクセスに制限なし
- ✅ 画像の永久保存

### 方法 B: Imgur（利用可能な場合）

**注意**: `https://api.imgur.com/oauth2/addclient`にアクセスできない場合、この方法は使えません。

1. [Imgur](https://imgur.com/)にアクセス
2. アカウント作成（無料）
3. ログイン後、以下のいずれかの方法で Client ID を取得:

   **方法 1**: 設定ページから

   - [アプリ設定ページ](https://imgur.com/account/settings/apps)にアクセス
   - 「Add application」または「Register an application」をクリック

   **方法 2**: 直接登録（アクセス可能な場合）

   - https://api.imgur.com/oauth2/addclient にアクセス
   - Authorization type: `OAuth 2 authorization without a callback URL`

4. **Client ID**をコピー

## 2. Render への環境変数設定

### 2.1 Render ダッシュボードで設定

1. [Render Dashboard](https://dashboard.render.com/)にログイン
2. あなたの Web Service を選択
3. 左メニューから「Environment」をクリック
4. 「Add Environment Variable」をクリック
5. 以下のいずれかを入力:

**ImgBB を使う場合（推奨）**:

- **Key**: `IMGBB_API_KEY`
- **Value**: コピーした API Key（例: `1234567890abcdef1234567890abcdef`）

**Imgur を使う場合**:

- **Key**: `IMGUR_CLIENT_ID`
- **Value**: コピーした Client ID（例: `abc123def456`）

**両方設定した場合**: ImgBB が優先的に使用され、失敗時に Imgur にフォールバックします。

6. 「Save Changes」をクリック

### 2.2 再デプロイ

環境変数を追加すると、自動的に再デプロイが開始されます。

## 3. 動作確認

### 3.1 LINE で確認

1. `?株` コマンドを実行
2. 銘柄一覧から任意の銘柄を選択
3. 「詳細を見る」をタップ
4. 銘柄詳細の後に**株価チャート画像**が表示されれば OK！

### 3.2 ログ確認

Render のログで以下のメッセージを確認:

**ImgBB の場合**:

```
[ImgBB] 画像アップロード成功: https://i.ibb.co/xxxxx/xxxxx.png
```

**Imgur の場合**:

```
[Imgur] 画像アップロード成功: https://i.imgur.com/xxxxx.png
```

## 4. トラブルシューティング

### チャートが表示されない場合

#### ケース 1: 環境変数未設定

**ログ**:

```
[ImgBB] IMGBB_API_KEYが設定されていません
[Imgur] IMGUR_CLIENT_IDが設定されていません
[画像アップロード] すべてのサービスが利用できません
```

**解決策**: 上記の「2. Render への環境変数設定」を実施（ImgBB 推奨）

#### ケース 2: API Key/Client ID が無効

**ログ**: `[ImgBB] HTTPエラー: 403` または `[Imgur] HTTPエラー: 403`

**解決策**:

- 新しい API Key を取得し直す
- ImgBB の場合: [API 設定ページ](https://api.imgbb.com/)で再取得
- Imgur の場合: 新しい Client ID を取得するか、**ImgBB に切り替える**（推奨）

#### ケース 3: matplotlib 未インストール

**ログ**: `[警告] matplotlib/japanize-matplotlibがインストールされていません`

**解決策**:

- `requirements.txt`に以下が含まれているか確認:
  ```
  matplotlib>=3.9.0
  japanize-matplotlib>=1.1.3
  ```
- Render で再デプロイ

#### ケース 4: requests ライブラリなし

**ログ**: `[Imgur] requestsライブラリが利用できません`

**解決策**:

- `requirements.txt`に`requests>=2.31.0`が追加されているか確認
- Render で再デプロイ

## 5. 料金・制限について

### ImgBB 無料プラン（推奨）

- **アップロード制限**: なし（無制限）
- **画像保存**: 無期限
- **帯域幅**: 無制限
- **商用利用**: 可能
- **利用規約**: [ImgBB Terms](https://imgbb.com/tos)

### Imgur 無料プラン

- **アップロード制限**: 50 画像/時間、1250 画像/日
- **画像保存**: 無期限（削除しない限り）
- **帯域幅**: 無制限
- **商用利用**: 可能
- **利用規約**: [Imgur API Terms](https://api.imgur.com/)

### どちらを選ぶべきか

**ImgBB を推奨する理由**:

- ✅ 登録が超簡単（1 分）
- ✅ アップロード無制限
- ✅ API 制限なし
- ✅ 2024 年以降も問題なくアクセス可能

**Imgur を選ぶ場合**:

- 既に Client ID を持っている
- より有名なサービスを使いたい

## 6. チャート機能の仕様

### 生成されるチャート

1. **株価推移チャート**

   - 銘柄詳細表示時に自動生成
   - 直近 30 日分の株価を折れ線グラフで表示

2. **ポートフォリオチャート**（将来実装予定）

   - 保有株の割合を円グラフで表示

3. **損益比較チャート**（将来実装予定）
   - 各銘柄の損益を棒グラフで表示

### 画像仕様

- **形式**: PNG
- **解像度**: 100 DPI
- **サイズ**: 約 100-200KB/枚
- **保存場所**: ImgBB または Imgur のクラウド
- **有効期限**: 無期限（両サービスとも）
- **アクセス**: 直リンク URL（LINE 上で即表示可能）

## 7. セキュリティ

### Client ID の管理

- ✅ **環境変数として保存**（Render Environment Variables）
- ❌ **コードにハードコードしない**
- ❌ **Git にコミットしない**

### アクセス制限

- Client ID は**読み取り専用**の操作のみ
- OAuth2 認証は不要（匿名アップロード）
- ユーザーデータへのアクセスなし

## 8. システムの動作仕様

### 画像アップロード優先順位

コードは以下の優先順位で画像アップロードを試行します:

1. **ImgBB** (`IMGBB_API_KEY`が設定されている場合)
2. **Imgur** (`IMGUR_CLIENT_ID`が設定されている場合)
3. 両方失敗 → チャート画像なしで詳細情報のみ表示

### フォールバック動作

```
ImgBB設定あり → ImgBBにアップロード試行
  ↓ 成功 → 画像表示
  ↓ 失敗
Imgur設定あり → Imgurにアップロード試行
  ↓ 成功 → 画像表示
  ↓ 失敗
チャート画像なしで詳細情報のみ表示
```

### 推奨設定

**最小限**:

- `IMGBB_API_KEY`のみ設定（ImgBB だけで十分）

**冗長性を持たせる場合**:

- `IMGBB_API_KEY`と`IMGUR_CLIENT_ID`の両方を設定
- どちらかが障害でも自動的にフォールバック

## 9. その他の画像サービス（参考）

### Cloudinary

- 無料枠: 25GB/月、25,000 リクエスト/月
- セットアップ: [Cloudinary API](https://cloudinary.com/)
- 実装変更が必要

コードを変更する場合は`apps/stock/chart_service.py`の`upload_image`メソッドを修正してください。
