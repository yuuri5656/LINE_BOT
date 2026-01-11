-- Add Gacha Token to CardMaster
INSERT INTO card_master (card_id, name, type, rarity, image_url, description) VALUES
(100, 'ガチャチケット', 'token', 'N', 'https://via.placeholder.com/150?text=Ticket', 'ガチャを引くためのチケット。')
ON CONFLICT (card_id) DO NOTHING;

-- Update GachaMaster to use Token
-- Assuming Gacha ID 1 is the Premium Gacha
UPDATE gacha_master 
SET cost_amount = 1, currency_type = 'TOKEN'
WHERE gacha_id = 1;

-- Add Shop Item (Gacha Token)
-- We need to check the next available item_id or let serial handle it.
-- Using explicit ID for seed script safety, assuming > 100 unused.
INSERT INTO shop_items (item_id, item_code, category, name, description, price, image_url) VALUES
(10, 'gacha_token_1', 'gacha_tokens', 'ガチャチケット x1', 'ガチャ1回分', 3000, 'https://via.placeholder.com/150?text=Ticketx1'),
(11, 'gacha_token_10', 'gacha_tokens', 'ガチャチケット x10', 'ガチャ10回分 (+おまけなし)', 30000, 'https://via.placeholder.com/150?text=Ticketx10')
ON CONFLICT (item_id) DO NOTHING;

-- Add Attributes
INSERT INTO shop_item_attributes (item_id, attribute_key, attribute_value, attribute_type) VALUES
(10, 'token_card_id', '100', 'integer'),
(10, 'amount', '1', 'integer'),
(11, 'token_card_id', '100', 'integer'),
(11, 'amount', '10', 'integer')
ON CONFLICT (item_id, attribute_key) DO NOTHING;
