-- ショップ商品の価格を1チップ=12円に更新
-- 実行日: 2025年12月2日

-- 既存のカジノチップ商品の価格を更新
-- chip_amountとbonus_chipの合計 × 12円に設定

-- 100チップ（ボーナス10枚）: (100 + 10) × 12 = 1320円
UPDATE shop_items
SET price = 1320.00
WHERE item_code = 'chip_100' AND category = 'casino_chips';

-- 500チップ（ボーナス75枚）: (500 + 75) × 12 = 6900円
UPDATE shop_items
SET price = 6900.00
WHERE item_code = 'chip_500' AND category = 'casino_chips';

-- 1000チップ（ボーナス200枚）: (1000 + 200) × 12 = 14400円
UPDATE shop_items
SET price = 14400.00
WHERE item_code = 'chip_1000' AND category = 'casino_chips';

-- 5000チップ（ボーナス1500枚）: (5000 + 1500) × 12 = 78000円
UPDATE shop_items
SET price = 78000.00
WHERE item_code = 'chip_5000' AND category = 'casino_chips';

-- 10000チップ（ボーナス3500枚）: (10000 + 3500) × 12 = 162000円
UPDATE shop_items
SET price = 162000.00
WHERE item_code = 'chip_10000' AND category = 'casino_chips';

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'ショップ商品の価格を1チップ=12円に更新しました。';
END $$;
