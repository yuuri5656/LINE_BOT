-- トランザクションテーブルに相手口座番号(other_account_number)カラムを追加
-- 実行日: 2025年12月1日

-- transactionsテーブルにother_account_numberカラムを追加
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS other_account_number TEXT;

-- インデックス追加（検索性能向上）
CREATE INDEX IF NOT EXISTS idx_transactions_other_account_number ON transactions(other_account_number);

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'transactionsテーブルにother_account_numberカラムを追加しました。';
END $$;
