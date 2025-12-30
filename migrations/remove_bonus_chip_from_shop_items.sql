-- ボーナスチップ廃止に伴うショップ商品データの修正
-- 実行日: 2025年12月28日
-- 目的:
-- - shop_items の説明文から「ボーナス」表記を撤去
-- - shop_item_attributes の bonus_chip 属性を削除（存在しない場合は何もしない）

BEGIN;

-- 1) チップ商品説明文の修正（item_codeで確実に対象を絞る）
UPDATE shop_items
SET
    description = 'ミニゲームで使える基本セット',
    updated_at = CURRENT_TIMESTAMP
WHERE item_code = 'CHIP_50';

UPDATE shop_items
SET
    description = '人気のスタンダードパック',
    updated_at = CURRENT_TIMESTAMP
WHERE item_code = 'CHIP_100';

UPDATE shop_items
SET
    description = '大容量パック',
    updated_at = CURRENT_TIMESTAMP
WHERE item_code = 'CHIP_200';

UPDATE shop_items
SET
    description = 'メガパック',
    updated_at = CURRENT_TIMESTAMP
WHERE item_code = 'CHIP_500';

-- 2) bonus_chip 属性の撤去
--    アプリ側は get_item_attribute(..., default=0) なので、属性が無くても問題なし。
DELETE FROM shop_item_attributes
WHERE attribute_key = 'bonus_chip'
  AND item_id IN (
      SELECT item_id
      FROM shop_items
      WHERE item_code IN ('CHIP_50', 'CHIP_100', 'CHIP_200', 'CHIP_500')
  );

-- 3) 念のため、チップ商品に bonus 関連の文言が残っていれば一括置換（他の商品にも効く）
--    （明示UPDATE済みの4商品以外で、同様の文言が残っている場合に備える）
UPDATE shop_items
SET
    description = REPLACE(REPLACE(REPLACE(description, '＋ボーナス', ''), '+ボーナス', ''), 'ボーナス', ''),
    updated_at = CURRENT_TIMESTAMP
WHERE category = 'casino_chips'
  AND description IS NOT NULL
  AND description LIKE '%ボーナス%';

COMMIT;

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'ボーナスチップ廃止: shop_items / shop_item_attributes の既存データ修正が完了しました。';
END $$;
