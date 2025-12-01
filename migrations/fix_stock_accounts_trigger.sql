-- stock_accountsテーブルのトリガーを削除
-- stock_accountsにはupdated_atカラムが存在しないため、このトリガーはエラーを引き起こす

-- トリガーが存在する場合のみ削除
DROP TRIGGER IF EXISTS update_stock_accounts_updated_at ON stock_accounts;

-- 確認メッセージ
DO $$
BEGIN
    RAISE NOTICE 'stock_accountsテーブルのupdated_atトリガーを削除しました';
END $$;
