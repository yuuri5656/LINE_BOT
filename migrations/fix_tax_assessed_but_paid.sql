-- 既に振込(=tax_payments)があるのに tax_assessments が未納(assessed等)のままのデータを特定し、納付済みに補正する。
-- 想定DB: PostgreSQL
--
-- 使い方:
-- 1) まず SELECT 部分だけ実行して対象が正しいか確認
-- 2) 問題なければ BEGIN〜COMMIT まで実行

BEGIN;

-- =============================
-- 1) 対象の特定（支払い合計が課税額以上、かつ status が paid 以外）
-- =============================
WITH pay AS (
  SELECT
    assessment_id,
    SUM(amount)                AS paid_amount,
    MAX(created_at)            AS latest_payment_at,
    MAX(bank_transaction_id)   AS any_bank_transaction_id
  FROM tax_payments
  GROUP BY assessment_id
)
SELECT
  a.assessment_id,
  a.user_id,
  a.period_id,
  a.status,
  a.tax_amount,
  pay.paid_amount,
  a.paid_at,
  pay.latest_payment_at,
  pay.any_bank_transaction_id
FROM tax_assessments a
JOIN pay ON pay.assessment_id = a.assessment_id
WHERE a.status <> 'paid'
  AND a.tax_amount > 0
  AND pay.paid_amount >= a.tax_amount
ORDER BY a.assessment_id DESC;

-- 対象ユーザー一覧（必要なら）
WITH pay AS (
  SELECT assessment_id, SUM(amount) AS paid_amount
  FROM tax_payments
  GROUP BY assessment_id
)
SELECT DISTINCT a.user_id
FROM tax_assessments a
JOIN pay ON pay.assessment_id = a.assessment_id
WHERE a.status <> 'paid'
  AND a.tax_amount > 0
  AND pay.paid_amount >= a.tax_amount
ORDER BY a.user_id;

-- =============================
-- 2) 更新対象を一時テーブルに固定（実行中に条件が変わっても安全）
-- =============================
DROP TABLE IF EXISTS tmp_fix_tax_paid;
CREATE TEMP TABLE tmp_fix_tax_paid AS
WITH pay AS (
  SELECT
    assessment_id,
    SUM(amount)     AS paid_amount,
    MAX(created_at) AS latest_payment_at
  FROM tax_payments
  GROUP BY assessment_id
)
SELECT
  a.assessment_id,
  pay.latest_payment_at
FROM tax_assessments a
JOIN pay ON pay.assessment_id = a.assessment_id
WHERE a.status <> 'paid'
  AND a.tax_amount > 0
  AND pay.paid_amount >= a.tax_amount;

-- 対象件数
SELECT COUNT(*) AS targets FROM tmp_fix_tax_paid;

-- =============================
-- 3) 納付済みに更新
-- =============================
UPDATE tax_assessments a
SET
  status = 'paid',
  paid_at = COALESCE(a.paid_at, t.latest_payment_at, now()),
  updated_at = now()
FROM tmp_fix_tax_paid t
WHERE a.assessment_id = t.assessment_id;

-- 更新結果の確認
SELECT
  a.assessment_id,
  a.user_id,
  a.status,
  a.tax_amount,
  a.paid_at,
  a.updated_at
FROM tax_assessments a
JOIN tmp_fix_tax_paid t ON t.assessment_id = a.assessment_id
ORDER BY a.assessment_id DESC;

COMMIT;

-- NOTE:
-- collections_cases 側も整合させたい場合は、別途以下のような補正を検討してください。
-- （既存運用により status 値が異なる可能性があるため、ここでは自動実行しない）
--
-- UPDATE collections_cases c
-- SET status = 'resolved', resolved_at = COALESCE(resolved_at, now()), updated_at = now()
-- FROM tmp_fix_tax_paid t
-- WHERE c.case_type = 'tax' AND c.reference_id = t.assessment_id AND c.status <> 'resolved';
