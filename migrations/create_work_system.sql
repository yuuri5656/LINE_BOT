-- 労働システム（会社）のデータベーステーブル作成
-- 実行日: 2025年12月2日

-- 会社（労働者）の給与振込口座登録テーブル
CREATE TABLE IF NOT EXISTS work_salary_accounts (
    salary_account_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_work_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

CREATE INDEX idx_work_salary_user_id ON work_salary_accounts(user_id);
CREATE INDEX idx_work_salary_last_work_at ON work_salary_accounts(last_work_at);

-- 労働履歴テーブル
CREATE TABLE IF NOT EXISTS work_history (
    work_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    salary_amount DECIMAL(15, 2) NOT NULL,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    worked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT '労働報酬'
);

CREATE INDEX idx_work_history_user_id ON work_history(user_id);
CREATE INDEX idx_work_history_worked_at ON work_history(worked_at DESC);

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE '労働システム（会社）のテーブル作成が完了しました。';
END $$;
