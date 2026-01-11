-- Gacha / Inventory / Trade System Initialization SQL
-- Execute this in your PostgreSQL database

BEGIN;

--------------------------------------------------------------------------------
-- Table Creation
--------------------------------------------------------------------------------

-- 1. Card Master
CREATE TABLE IF NOT EXISTS card_master (
    card_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'character', 'skill', 'skin'
    rarity VARCHAR(10) NOT NULL, -- 'UR', 'SSR', 'SR', 'R', 'N'
    description VARCHAR,
    image_url VARCHAR,
    attributes JSONB,
    effects JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 2. Gacha Master
CREATE TABLE IF NOT EXISTS gacha_master (
    gacha_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    banner_image_url VARCHAR,
    cost_amount NUMERIC(18, 2) NOT NULL,
    currency_type VARCHAR(50) DEFAULT 'JPY',
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 3. Gacha Items
CREATE TABLE IF NOT EXISTS gacha_items (
    id SERIAL PRIMARY KEY,
    gacha_id INTEGER NOT NULL REFERENCES gacha_master(gacha_id) ON DELETE CASCADE,
    card_id INTEGER NOT NULL REFERENCES card_master(card_id) ON DELETE CASCADE,
    weight INTEGER NOT NULL DEFAULT 1,
    is_pickup BOOLEAN DEFAULT false
);

-- 4. User Collections
CREATE TABLE IF NOT EXISTS user_collections (
    collection_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    card_id INTEGER NOT NULL REFERENCES card_master(card_id),
    quantity INTEGER NOT NULL DEFAULT 0,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 5. User Equipment
CREATE TABLE IF NOT EXISTS user_equipment (
    equipment_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    slot_type VARCHAR(50) NOT NULL, -- 'character', 'skill_1' etc
    card_id INTEGER REFERENCES card_master(card_id),
    equipped_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 6. Trade Requests
CREATE TABLE IF NOT EXISTS trade_requests (
    trade_id SERIAL PRIMARY KEY,
    sender_id VARCHAR(255) NOT NULL,
    receiver_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 7. Trade Items
CREATE TABLE IF NOT EXISTS trade_items (
    item_id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trade_requests(trade_id) ON DELETE CASCADE,
    owner_id VARCHAR(255) NOT NULL,
    item_type VARCHAR(50) NOT NULL, -- 'card', 'currency'
    card_id INTEGER REFERENCES card_master(card_id),
    quantity INTEGER,
    currency_type VARCHAR(50),
    amount NUMERIC(18, 2)
);

--------------------------------------------------------------------------------
-- Seed Data
--------------------------------------------------------------------------------

-- Insert Cards
INSERT INTO card_master (card_id, name, type, rarity, image_url, description, attributes, effects) VALUES
(1, '塩爺 (Normal)', 'character', 'N', 'https://via.placeholder.com/150?text=Shiojii+N', '普通の塩爺。', NULL, NULL),
(2, '塩爺 (SSR メスガキ)', 'character', 'SSR', 'https://via.placeholder.com/150/FF00FF/FFFFFF?text=Mesugaki', 'メスガキ化した塩爺。「ざぁこ♡」', '{"style": "mesugaki"}', NULL),
(3, '株式手数料カット (Normal)', 'skill', 'N', 'https://via.placeholder.com/150?text=Fee-1%', '株売却手数料 -1%', NULL, '[{"target": "stock_sell_fee_reduction", "value": 0.01}]'),
(4, '株式手数料カット (SSR)', 'skill', 'SSR', 'https://via.placeholder.com/150/Gold?text=Fee-50%', '株売却手数料 -50%', NULL, '[{"target": "stock_sell_fee_reduction", "value": 0.50}]'),
(5, '塩爺の杖', 'skin', 'R', 'https://via.placeholder.com/150?text=Cane', 'ただの杖。', NULL, NULL)
ON CONFLICT (card_id) DO NOTHING;

-- Reset sequence if needed (Optional, prevents collision if auto-increment was used before)
SELECT setval('card_master_card_id_seq', (SELECT MAX(card_id) FROM card_master));

-- Insert Gacha Banner
INSERT INTO gacha_master (gacha_id, name, description, cost_amount, currency_type, banner_image_url) VALUES
(1, '塩爺プレミアムガチャ', 'メスガキ塩爺が出るかも！？', 3000, 'JPY', 'https://via.placeholder.com/300x150?text=Premium+Gacha')
ON CONFLICT (gacha_id) DO NOTHING;

SELECT setval('gacha_master_gacha_id_seq', (SELECT MAX(gacha_id) FROM gacha_master));

-- Insert Gacha Items
INSERT INTO gacha_items (gacha_id, card_id, weight) VALUES
(1, 1, 50), -- N Shiojii
(1, 2, 5),  -- SSR Mesugaki
(1, 3, 30), -- N Skill
(1, 4, 2),  -- SSR Skill
(1, 5, 13); -- R Skin

COMMIT;
