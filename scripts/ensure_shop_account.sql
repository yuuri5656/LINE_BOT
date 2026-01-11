-- Ensure Shop Operations Account exists
BEGIN;

-- 1. Create Branch if not exists (001)
INSERT INTO branches (code, name) VALUES ('001', '本店') ON CONFLICT (code) DO NOTHING;

-- 2. Create Customer (Shop Admin)
INSERT INTO customers (full_name, date_of_birth, user_id)
SELECT 'ｼｮｯﾌﾟ ｳﾝｴｲ', '2000-01-01', 'SHOP_ADMIN'
WHERE NOT EXISTS (
    SELECT 1 FROM customers WHERE user_id = 'SHOP_ADMIN'
);

-- 3. Create Account
-- Account Number: 2103737
INSERT INTO accounts (customer_id, user_id, account_number, balance, currency, status, type, branch_id)
SELECT 
    c.customer_id,
    c.user_id,
    '2103737',
    0,
    'JPY',
    'active'::account_status,
    'ordinary'::account_type,
    b.branch_id
FROM customers c
CROSS JOIN branches b
WHERE c.user_id = 'SHOP_ADMIN' AND b.code = '001'
AND NOT EXISTS (
    SELECT 1 FROM accounts WHERE account_number = '2103737'
);

COMMIT;
