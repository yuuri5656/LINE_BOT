-- 借金(ローン/リボ) システム
-- - 回収（督促/延滞/差押え）は collections_cases と連携

BEGIN;

CREATE TABLE IF NOT EXISTS loans (
    loan_id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    principal NUMERIC(18,2) NOT NULL,
    outstanding_balance NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    interest_weekly_rate NUMERIC(10,6) NOT NULL,
    interest_weekly_rate_cap_applied NUMERIC(10,6) NOT NULL,
    late_interest_weekly_rate NUMERIC(10,6) NOT NULL DEFAULT 0.200000,
    autopay_account_id BIGINT REFERENCES accounts(account_id) ON DELETE SET NULL,
    autopay_amount NUMERIC(18,2) NOT NULL DEFAULT 1000,
    last_autopay_attempt_at TIMESTAMPTZ,
    autopay_failed_since TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_loans_status CHECK (status IN ('active','resolved')),
    CONSTRAINT chk_loans_amounts CHECK (principal >= 0 AND outstanding_balance >= 0)
);
CREATE INDEX IF NOT EXISTS idx_loans_user_status ON loans(user_id, status);

CREATE TABLE IF NOT EXISTS loan_payments (
    payment_id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    bank_transaction_id BIGINT REFERENCES transactions(transaction_id) ON DELETE SET NULL,
    amount NUMERIC(18,2) NOT NULL,
    paid_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_time ON loan_payments(loan_id, paid_at);

COMMIT;
