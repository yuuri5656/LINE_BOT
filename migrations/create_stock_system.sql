-- 株式トレードシステムのデータベーステーブル作成
-- 実行日: 2025年11月29日

-- 株式銘柄マスタテーブル
CREATE TABLE IF NOT EXISTS stock_symbols (
    symbol_id SERIAL PRIMARY KEY,
    symbol_code VARCHAR(10) NOT NULL UNIQUE, -- '9999', '8888', etc.
    name VARCHAR(255) NOT NULL,               -- 'テクノロジー株式会社'
    sector VARCHAR(100) NOT NULL,             -- '情報・通信', '銀行', etc.
    initial_price INTEGER NOT NULL,           -- 初期価格
    current_price INTEGER NOT NULL,           -- 現在価格
    volatility DECIMAL(5, 4) NOT NULL,        -- ボラティリティ (0.0200 = 2%)
    dividend_yield DECIMAL(5, 2) NOT NULL,    -- 配当利回り (%)
    market_cap BIGINT,                        -- 時価総額
    description TEXT,                         -- 企業説明
    is_tradable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_symbols_code ON stock_symbols(symbol_code);
CREATE INDEX idx_stock_symbols_sector ON stock_symbols(sector);

-- 株価履歴テーブル
CREATE TABLE IF NOT EXISTS stock_price_history (
    price_id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id) ON DELETE CASCADE,
    price INTEGER NOT NULL,
    volume INTEGER NOT NULL,                   -- 出来高
    daily_high INTEGER,                        -- 日中高値
    daily_low INTEGER,                         -- 日中安値
    trend DECIMAL(8, 6),                       -- トレンド値
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_price_symbol_id ON stock_price_history(symbol_id);
CREATE INDEX idx_stock_price_timestamp ON stock_price_history(timestamp DESC);

-- 株式用口座テーブル
CREATE TABLE IF NOT EXISTS stock_accounts (
    stock_account_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    linked_bank_account_id INTEGER NOT NULL,        -- 外部キー制約なし（アプリケーション層で整合性管理）
    cash_balance DECIMAL(18, 2) DEFAULT 0 NOT NULL, -- 現金残高（証券口座内）
    total_value DECIMAL(18, 2) DEFAULT 0,           -- 総資産評価額
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_traded_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_stock_accounts_user_id ON stock_accounts(user_id);

-- ユーザー株式保有テーブル
CREATE TABLE IF NOT EXISTS user_stock_holdings (
    holding_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    average_price DECIMAL(18, 4) NOT NULL,     -- 平均取得単価
    total_cost DECIMAL(18, 2) NOT NULL,        -- 総取得コスト
    stock_account_id INTEGER NOT NULL REFERENCES stock_accounts(stock_account_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol_id)
);

CREATE INDEX idx_user_holdings_user_id ON user_stock_holdings(user_id);
CREATE INDEX idx_user_holdings_symbol_id ON user_stock_holdings(symbol_id);

-- 株式取引履歴テーブル
CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    trade_type VARCHAR(10) NOT NULL,           -- 'buy', 'sell'
    quantity INTEGER NOT NULL,
    price DECIMAL(18, 4) NOT NULL,             -- 約定価格
    total_amount DECIMAL(18, 2) NOT NULL,      -- 総額
    fee DECIMAL(18, 2) DEFAULT 0,              -- 手数料
    stock_account_id INTEGER NOT NULL REFERENCES stock_accounts(stock_account_id),
    status VARCHAR(50) DEFAULT 'completed',    -- 'pending', 'completed', 'failed'
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_tx_user_id ON stock_transactions(user_id);
CREATE INDEX idx_stock_tx_symbol_id ON stock_transactions(symbol_id);
CREATE INDEX idx_stock_tx_executed_at ON stock_transactions(executed_at DESC);

-- AIトレーダーテーブル
CREATE TABLE IF NOT EXISTS ai_traders (
    trader_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    strategy VARCHAR(50) NOT NULL,             -- 'momentum', 'reversal', 'value', 'scalping', 'random'
    risk_level VARCHAR(50) NOT NULL,           -- 'conservative', 'moderate', 'aggressive', 'extreme'
    cash DECIMAL(18, 2) NOT NULL,
    patience DECIMAL(3, 2),                    -- 忍耐力 0.00-1.00
    greed DECIMAL(3, 2),                       -- 欲深さ 0.00-1.00
    fear DECIMAL(3, 2),                        -- 恐怖心 0.00-1.00
    confidence DECIMAL(3, 2),                  -- 自信 0.00-1.00
    contrarian DECIMAL(3, 2),                  -- 逆張り度 0.00-1.00
    herd_mentality DECIMAL(3, 2),              -- 群衆心理 0.00-1.00
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_traders_strategy ON ai_traders(strategy);

-- AIトレーダー保有株テーブル
CREATE TABLE IF NOT EXISTS ai_trader_holdings (
    ai_holding_id SERIAL PRIMARY KEY,
    trader_id INTEGER NOT NULL REFERENCES ai_traders(trader_id),
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    average_price DECIMAL(18, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trader_id, symbol_id)
);

CREATE INDEX idx_ai_holdings_trader_id ON ai_trader_holdings(trader_id);
CREATE INDEX idx_ai_holdings_symbol_id ON ai_trader_holdings(symbol_id);

-- AIトレーダー取引履歴テーブル
CREATE TABLE IF NOT EXISTS ai_trader_transactions (
    ai_transaction_id SERIAL PRIMARY KEY,
    trader_id INTEGER NOT NULL REFERENCES ai_traders(trader_id),
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    trade_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(18, 4) NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_tx_trader_id ON ai_trader_transactions(trader_id);
CREATE INDEX idx_ai_tx_symbol_id ON ai_trader_transactions(symbol_id);
CREATE INDEX idx_ai_tx_executed_at ON ai_trader_transactions(executed_at DESC);

-- 経済イベントテーブル
CREATE TABLE IF NOT EXISTS stock_events (
    event_id SERIAL PRIMARY KEY,
    symbol_id INTEGER REFERENCES stock_symbols(symbol_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,           -- 'news', 'earnings', 'scandal', 'product_launch', 'market_crash'
    event_text TEXT NOT NULL,
    impact DECIMAL(6, 4) NOT NULL,             -- 株価への影響度 (-0.3000 ~ +0.3000)
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_events_symbol_id ON stock_events(symbol_id);
CREATE INDEX idx_stock_events_occurred_at ON stock_events(occurred_at DESC);

-- 配当金支払い履歴テーブル
CREATE TABLE IF NOT EXISTS dividend_payments (
    dividend_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    quantity INTEGER NOT NULL,
    dividend_per_share DECIMAL(18, 4) NOT NULL,
    total_dividend DECIMAL(18, 2) NOT NULL,
    stock_account_id INTEGER NOT NULL REFERENCES stock_accounts(stock_account_id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dividends_user_id ON dividend_payments(user_id);
CREATE INDEX idx_dividends_payment_date ON dividend_payments(payment_date DESC);

-- トリガー: updated_at自動更新
CREATE TRIGGER update_stock_symbols_updated_at
BEFORE UPDATE ON stock_symbols
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_holdings_updated_at
BEFORE UPDATE ON user_stock_holdings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_holdings_updated_at
BEFORE UPDATE ON ai_trader_holdings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- stock_accountsにはupdated_atカラムがないため、トリガーは設定しない
-- (last_traded_atは手動で更新)

-- 初期銘柄データ挿入（10銘柄）
INSERT INTO stock_symbols (symbol_code, name, sector, initial_price, current_price, volatility, dividend_yield, market_cap, description) VALUES
('9999', 'エムヴィディア', '情報・通信', 2500, 2500, 0.0400, 1.20, 500000000000, '最先端のAI技術とクラウドサービスを提供する大手IT企業。成長性が高く取引されています。'),
('8888', '(株)塩路本田フィナンシャルグループ', '銀行', 1800, 1800, 0.0200, 3.50, 800000000000, '世界最大手の都市銀行。他に類を見ないほど極めて安定した経営基盤と、高配当が魅力のディフェンシブ銘柄です。'),
('7777', '東海電力(株)', 'エネルギー', 3200, 3200, 0.0350, 2.80, 400000000000, '再生可能エネルギーと従来型エネルギーの両輪で事業展開。政策の影響を受けやすい銘柄。'),
('6666', '第二四共(株)', '医薬品', 4500, 4500, 0.0250, 2.00, 600000000000, '新薬開発に強みを持つ製薬会社。安定した需要と高い研究開発力が特徴です。'),
('5555', 'ニッサソ自動車(株)', '自動車', 1500, 1500, 0.0380, 2.50, 700000000000, '電気自動車への転換を進める大手自動車メーカー。景気敏感株として知られています。'),
('4444', '(株)シックス＆アイ・ホールディングス', '小売', 2200, 2200, 0.0300, 2.20, 300000000000, '全国展開する大型小売チェーン。消費動向の影響を受けやすい銘柄です。'),
('3333', '杉村不動産マスターファンド投資法人', '不動産', 5000, 5000, 0.0200, 4.50, 250000000000, '優良オフィスビルを中心に運用するREIT。高配当が魅力の安定銘柄です。'),
('2222', '大正ホールディングス(株)', '食品', 1200, 1200, 0.0180, 3.00, 350000000000, '加工食品と飲料を製造する老舗企業。景気に左右されにくいディフェンシブ銘柄。'),
('1111', '(株)小林組', '建設', 980, 980, 0.0320, 3.20, 200000000000, '公共事業と民間建設の両方を手掛ける総合建設会社。割安感のある銘柄です。'),
('0001', 'レイヤーワイ(株)', '情報・通信', 800, 800, 0.0800, 0.00, 50000000000, '急成長中のスタートアップ企業。超ハイリスク・ハイリターンのグロース株です。')
ON CONFLICT (symbol_code) DO NOTHING;

-- 初期AIトレーダー生成（30体）
DO $$
DECLARE
    strategies TEXT[] := ARRAY['momentum', 'reversal', 'value', 'scalping', 'random', 'growth', 'day_trader', 'swing', 'long_term'];
    risk_levels TEXT[] := ARRAY['conservative', 'moderate', 'aggressive', 'extreme'];
    names TEXT[] := ARRAY['山田太郎', '鈴木花子', '佐藤武', '田中美咲', '伊藤健太', '渡辺あかり', '中村雄大', '小林さくら', '加藤竜也', '吉田麗奈',
                          '高橋誠', '松本美優', '井上大輔', '木村さやか', '林健一', '清水恵', '山崎拓也', '森田愛', '池田翔太', '橋本結衣',
                          '石川浩二', '前田奈々', '岡田和也', '長谷川舞', '藤田雅人', '村上彩', '近藤悠斗', '斎藤莉子', '遠藤幸太', '青木美穂'];
    i INTEGER;
BEGIN
    FOR i IN 1..30 LOOP
        INSERT INTO ai_traders (name, strategy, risk_level, cash, patience, greed, fear, confidence, contrarian, herd_mentality)
        VALUES (
            names[i] || '#' || i,
            strategies[1 + (i % array_length(strategies, 1))],
            risk_levels[1 + ((i * 3) % array_length(risk_levels, 1))],
            500000 + (random() * 1500000)::INTEGER,
            random(),
            random(),
            random(),
            random(),
            random(),
            random()
        );
    END LOOP;
END $$;

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE '株式トレードシステムのテーブル作成が完了しました。';
    RAISE NOTICE '初期データ: 銘柄10種類、AIトレーダー30体が登録されました。';
END $$;
