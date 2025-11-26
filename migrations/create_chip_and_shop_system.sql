-- チップシステムとショップ機能のデータベーステーブル作成
-- 実行日: 2025年11月26日

-- チップ残高テーブル
CREATE TABLE IF NOT EXISTS minigame_chips (
    chip_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (balance >= 0),
    locked_balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (locked_balance >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT available_balance_check CHECK (balance >= locked_balance)
);

CREATE INDEX idx_chips_user_id ON minigame_chips(user_id);

-- チップ取引履歴テーブル
CREATE TABLE IF NOT EXISTS chip_transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    balance_after DECIMAL(15, 2) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'purchase', 'transfer_in', 'transfer_out', 'game_bet', 'game_win', 'game_refund'
    related_user_id VARCHAR(255), -- 送信先/送信元ユーザーID（transfer時）
    game_session_id VARCHAR(255), -- ゲームセッションID
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chip_tx_user_id ON chip_transactions(user_id);
CREATE INDEX idx_chip_tx_created_at ON chip_transactions(created_at DESC);
CREATE INDEX idx_chip_tx_type ON chip_transactions(type);

-- ショップ支払い用口座登録テーブル
CREATE TABLE IF NOT EXISTS shop_payment_accounts (
    payment_account_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

CREATE INDEX idx_shop_payment_user_id ON shop_payment_accounts(user_id);

-- ショップ商品マスタテーブル（汎用設計）
CREATE TABLE IF NOT EXISTS shop_items (
    item_id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL, -- 'casino_chips', 'special_items', 'boosters'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(15, 2) NOT NULL,
    stock INTEGER DEFAULT -1, -- -1は無制限
    is_available BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shop_items_category ON shop_items(category);
CREATE INDEX idx_shop_items_available ON shop_items(is_available);

-- 商品属性テーブル（EAVパターン）
CREATE TABLE IF NOT EXISTS shop_item_attributes (
    attribute_id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES shop_items(item_id) ON DELETE CASCADE,
    attribute_key VARCHAR(100) NOT NULL, -- 'chip_amount', 'bonus_chip', 'duration_days', 'boost_rate' など
    attribute_value TEXT NOT NULL,
    attribute_type VARCHAR(50) DEFAULT 'string', -- 'string', 'integer', 'decimal', 'boolean', 'json'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shop_item_attributes_item_id ON shop_item_attributes(item_id);
CREATE INDEX idx_shop_item_attributes_key ON shop_item_attributes(attribute_key);
CREATE UNIQUE INDEX idx_shop_item_attributes_unique ON shop_item_attributes(item_id, attribute_key);

-- ショップ購入履歴テーブル
CREATE TABLE IF NOT EXISTS shop_purchases (
    purchase_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id INTEGER NOT NULL REFERENCES shop_items(item_id),
    quantity INTEGER DEFAULT 1,
    total_price DECIMAL(15, 2) NOT NULL,
    payment_account_id INTEGER REFERENCES accounts(account_id),
    status VARCHAR(50) DEFAULT 'completed', -- 'completed', 'failed', 'refunded'
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shop_purchases_user_id ON shop_purchases(user_id);
CREATE INDEX idx_shop_purchases_purchased_at ON shop_purchases(purchased_at DESC);

-- 初期チップ商品データ挿入
INSERT INTO shop_items (item_code, category, name, description, price, display_order) VALUES
('CHIP_50', 'casino_chips', 'チップ50枚', 'ミニゲームで使える基本セット', 50, 1),
('CHIP_100', 'casino_chips', 'チップ100枚', '人気のスタンダードパック＋ボーナス', 100, 2),
('CHIP_200', 'casino_chips', 'チップ200枚', '大容量パック＋ボーナス', 200, 3),
('CHIP_500', 'casino_chips', 'チップ500枚', 'メガパック＋大ボーナス！', 500, 4)
ON CONFLICT (item_code) DO NOTHING;

-- チップ商品の属性を挿入
INSERT INTO shop_item_attributes (item_id, attribute_key, attribute_value, attribute_type) VALUES
((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_50'), 'chip_amount', '50', 'integer'),
((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_50'), 'bonus_chip', '2', 'integer'),

((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_100'), 'chip_amount', '100', 'integer'),
((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_100'), 'bonus_chip', '5', 'integer'),

((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_200'), 'chip_amount', '200', 'integer'),
((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_200'), 'bonus_chip', '15', 'integer'),

((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_500'), 'chip_amount', '500', 'integer'),
((SELECT item_id FROM shop_items WHERE item_code = 'CHIP_500'), 'bonus_chip', '50', 'integer')
ON CONFLICT (item_id, attribute_key) DO NOTHING;

-- トリガー: updated_at自動更新
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_minigame_chips_updated_at
BEFORE UPDATE ON minigame_chips
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shop_items_updated_at
BEFORE UPDATE ON shop_items
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'チップシステムとショップ機能のテーブル作成が完了しました。';
    RAISE NOTICE '初期データ: チップ商品4種類が登録されました。';
END $$;
