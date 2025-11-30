-- 外部キー制約削除マイグレーション
-- 実行日: 2025年11月30日

-- stock_accounts テーブルの外部キー制約を削除
-- （異なるSQLAlchemyエンジン間での外部キー参照を回避）

DO $$
BEGIN
    -- 外部キー制約が存在する場合のみ削除
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'stock_accounts_linked_bank_account_id_fkey'
        AND table_name = 'stock_accounts'
    ) THEN
        ALTER TABLE stock_accounts
        DROP CONSTRAINT stock_accounts_linked_bank_account_id_fkey;

        RAISE NOTICE '外部キー制約を削除しました: stock_accounts_linked_bank_account_id_fkey';
    ELSE
        RAISE NOTICE '外部キー制約は存在しません（スキップ）';
    END IF;
END $$;

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'マイグレーション完了: 外部キー制約の削除';
END $$;
