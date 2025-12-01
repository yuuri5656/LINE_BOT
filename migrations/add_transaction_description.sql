-- トランザクションテーブルに摘要(description)カラムを追加
-- 実行日: 2025年12月1日

-- transactionsテーブルにdescriptionカラムを追加
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS description TEXT;

-- 既存データに説明を追加（オプション）
UPDATE transactions
SET description = CASE
    WHEN type = 'transfer' THEN '振込'
    WHEN type = 'deposit' THEN '入金'
    WHEN type = 'withdrawal' THEN '出金'
    WHEN type = 'fee' THEN '手数料'
    WHEN type = 'interest' THEN '利息'
    ELSE type::TEXT
END
WHERE description IS NULL;

-- インデックス追加（検索性能向上）
CREATE INDEX IF NOT EXISTS idx_transactions_description ON transactions(description);

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'transactionsテーブルにdescriptionカラムを追加しました。';
END $$;
