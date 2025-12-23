-- 税金 + 回収(督促/延滞/ブラックリスト/差押え) 統合基盤
-- 方針:
-- - 将来拡張しやすいよう、ENUM型を新規に作らず text + CHECK を基本にする
-- - 既存の banking の transactions/accounts と FK で接続できる形にする

BEGIN;

-- =============================
-- ブラックリスト（信用情報）
-- =============================
CREATE TABLE IF NOT EXISTS credit_profile (
    user_id TEXT PRIMARY KEY,
    is_blacklisted BOOLEAN NOT NULL DEFAULT FALSE,
    blacklisted_at TIMESTAMPTZ,
    blacklisted_reason TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================
-- 税: 納税口座設定
-- =============================
CREATE TABLE IF NOT EXISTS tax_profiles (
    user_id TEXT PRIMARY KEY,
    tax_account_id BIGINT REFERENCES accounts(account_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================
-- 税: 週次期間
-- =============================
CREATE TABLE IF NOT EXISTS tax_periods (
    period_id BIGSERIAL PRIMARY KEY,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (start_at, end_at)
);

-- =============================
-- 税: 所得イベント台帳
-- =============================
CREATE TABLE IF NOT EXISTS tax_income_events (
    event_id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    taxable_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL,
    source_id BIGINT NOT NULL,
    meta_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_type, source_id)
);
CREATE INDEX IF NOT EXISTS idx_tax_income_events_user_time ON tax_income_events(user_id, occurred_at);

-- =============================
-- 税: 課税（週次）
-- =============================
CREATE TABLE IF NOT EXISTS tax_assessments (
    assessment_id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    period_id BIGINT NOT NULL REFERENCES tax_periods(period_id) ON DELETE CASCADE,
    total_income NUMERIC(18,2) NOT NULL,
    taxable_income NUMERIC(18,2) NOT NULL,
    tax_amount NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_at TIMESTAMPTZ NOT NULL,
    payment_window_end_at TIMESTAMPTZ NOT NULL,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_tax_assessments_status CHECK (status IN ('assessed','paid','overdue','seizure')),
    UNIQUE (user_id, period_id)
);
CREATE INDEX IF NOT EXISTS idx_tax_assessments_user_status ON tax_assessments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tax_assessments_status_due ON tax_assessments(status, due_at);

-- =============================
-- 税: 納付記録（銀行取引とリンク）
-- =============================
CREATE TABLE IF NOT EXISTS tax_payments (
    payment_id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT NOT NULL REFERENCES tax_assessments(assessment_id) ON DELETE CASCADE,
    bank_transaction_id BIGINT REFERENCES transactions(transaction_id) ON DELETE SET NULL,
    amount NUMERIC(18,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tax_payments_assessment ON tax_payments(assessment_id);

-- =============================
-- 回収ケース（税/ローン共通）
-- =============================
CREATE TABLE IF NOT EXISTS collections_cases (
    case_id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    reference_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    due_at TIMESTAMPTZ,
    payment_window_end_at TIMESTAMPTZ,
    overdue_started_at TIMESTAMPTZ,
    blacklisted_at TIMESTAMPTZ,
    seizure_started_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    last_inline_notice_at TIMESTAMPTZ,
    last_push_notice_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    push_notice_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_collections_cases_type CHECK (case_type IN ('tax','loan')),
    CONSTRAINT chk_collections_cases_status CHECK (status IN ('open','in_payment_window','overdue','seizure','resolved')),
    UNIQUE (case_type, reference_id)
);
CREATE INDEX IF NOT EXISTS idx_collections_cases_user_status ON collections_cases(user_id, status);
CREATE INDEX IF NOT EXISTS idx_collections_cases_status ON collections_cases(status);

-- =============================
-- 回収：日次増分（延滞税/遅延損害金/利息）
-- =============================
CREATE TABLE IF NOT EXISTS collections_accruals (
    accrual_id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL REFERENCES collections_cases(case_id) ON DELETE CASCADE,
    accrual_type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    principal_base NUMERIC(18,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days INTEGER NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_collections_accruals_type CHECK (accrual_type IN ('tax_penalty','loan_interest','loan_late_interest'))
);
CREATE INDEX IF NOT EXISTS idx_collections_accruals_case_date ON collections_accruals(case_id, end_date);

-- =============================
-- 回収：監査ログ（いつ何をしたか）
-- =============================
CREATE TABLE IF NOT EXISTS collections_events (
    event_id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL REFERENCES collections_cases(case_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    note TEXT,
    meta_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_collections_events_case_time ON collections_events(case_id, created_at);

COMMIT;
