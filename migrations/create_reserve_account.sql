-- 銀行準備預金口座の作成
-- 実行日: 2025年12月1日
-- 株式売買と配当金の決済に使用する中央口座

-- まず、システム用の顧客を作成（存在しない場合）
INSERT INTO customers (user_id, full_name, full_name_kana, birth_date, phone, email, created_at)
VALUES
    ('SYSTEM_RESERVE', '準備預金口座', 'ジユンビヨキン', '2000-01-01', NULL, NULL, CURRENT_TIMESTAMP)
ON CONFLICT (user_id) DO NOTHING;

-- 支店001が存在することを確認（なければ作成）
INSERT INTO branches (code, name, address, created_at)
VALUES
    ('001', '本店', '東京都千代田区', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 準備預金口座を作成（口座番号: 7777777）
DO $$
DECLARE
    v_customer_id BIGINT;
    v_branch_id INTEGER;
BEGIN
    -- 顧客IDを取得
    SELECT customer_id INTO v_customer_id
    FROM customers
    WHERE user_id = 'SYSTEM_RESERVE';

    -- 支店IDを取得
    SELECT branch_id INTO v_branch_id
    FROM branches
    WHERE code = '001';

    -- 準備預金口座を作成
    INSERT INTO accounts (
        customer_id,
        user_id,
        account_number,
        balance,
        currency,
        status,
        type,
        branch_id,
        created_at,
        updated_at
    )
    VALUES (
        v_customer_id,
        'SYSTEM_RESERVE',
        '7777777',
        9999999999.00,  -- 初期残高: 約100億円
        'JPY',
        'active',
        'ordinary',
        v_branch_id,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (account_number) DO UPDATE
    SET balance = EXCLUDED.balance;

    RAISE NOTICE '準備預金口座 (001-7777777) を作成しました。';
END $$;
