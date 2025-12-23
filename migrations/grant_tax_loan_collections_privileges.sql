-- NOTE:
-- 本番でアプリ接続ユーザーとマイグレーション実行ユーザーが異なる場合、
-- 新規テーブルへの権限不足で runtime が落ちることがある。
-- ここでは簡易に PUBLIC へ権限を付与する。
-- 必要に応じて PUBLIC をアプリ用ロールへ置き換えてください。

BEGIN;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
  tax_profiles,
  tax_periods,
  tax_income_events,
  tax_assessments,
  tax_payments,
  credit_profile,
  collections_cases,
  collections_accruals,
  collections_events,
  loans,
  loan_payments
TO PUBLIC;

-- シーケンスがある場合の権限（BIGSERIAL等）
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;

COMMIT;
