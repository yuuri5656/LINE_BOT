-- 懲役システム用テーブル定義
-- 2025年12月12日 作成

-- ============================================
-- 1. 懲役情報テーブル (prison_sentences)
-- ============================================
CREATE TABLE IF NOT EXISTS prison_sentences (
    sentence_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    start_date DATE NOT NULL,           -- 施行日
    end_date DATE NOT NULL,             -- 釈放日
    initial_days INTEGER NOT NULL,      -- 初期懲役日数
    remaining_days INTEGER NOT NULL,    -- 残り懲役日数
    daily_quota INTEGER NOT NULL,       -- 1日のノルマ（?労働回数）
    completed_today INTEGER DEFAULT 0,  -- 今日の?労働実行回数
    last_work_date DATE,                -- 最後に?労働を実行した日付
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    FOREIGN KEY (user_id) REFERENCES customers(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_prison_user_id ON prison_sentences(user_id);
CREATE INDEX idx_prison_end_date ON prison_sentences(end_date);

-- ============================================
-- 2. 犯罪者更生給付金口座テーブル
-- ============================================
CREATE TABLE IF NOT EXISTS prison_rehabilitation_fund (
    fund_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,        -- 準備預金口座と同じ概念の会計用口座
    total_collected NUMERIC(15,2) DEFAULT 0,  -- 累計収集額
    last_distribution_date DATE,        -- 最後に分配した日付
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

CREATE INDEX idx_prison_fund_account ON prison_rehabilitation_fund(account_id);

-- ============================================
-- 3. 給付金分配履歴テーブル
-- ============================================
CREATE TABLE IF NOT EXISTS prison_rehabilitation_distributions (
    distribution_id SERIAL PRIMARY KEY,
    distribution_date DATE NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,
    recipient_count INTEGER NOT NULL,
    amount_per_recipient NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_prison_dist_date ON prison_rehabilitation_distributions(distribution_date);

-- ============================================
-- ステータスメッセージ
-- ============================================
-- 懲役システム用テーブルの作成が完了しました
-- 既存テーブルの account_status ENUM に 'frozen' ステータスがあることを確認してください
