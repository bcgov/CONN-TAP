-- =====================================================================
-- Regression check for the hardware-detail matching change in telus.sql
-- ---------------------------------------------------------------------
-- telus.sql used to match hardware detail_descriptions as literal text.
-- It now reduces each description to its word signature (parentheses
-- dropped, every non-letter character removed) and matches on that, so
-- Telus's variable amounts / terms / expiry dates collapse to one entry.
--
-- Two separate changes shipped together, and these queries separate them:
--   1. the matching mechanism  (literal -> word signature)
--   2. the seven newly confirmed hardware families (March 2026)
--
-- QUERY 1 proves change 1 is a no-op. QUERY 2 prices change 2.
-- Run both against the same database telus.sql is run against.
-- =====================================================================


-- =====================================================================
-- QUERY 1 -- Does normalization alone change any classification?
-- ---------------------------------------------------------------------
-- Compares the OLD literal match against the NEW word-signature match
-- using ONLY the original eight descriptions -- the seven new families
-- are deliberately excluded here, so any row returned is caused purely
-- by the change of mechanism.
--
-- EXPECTED RESULT: 0 rows.
--
-- is_hw is the only input the rest of telus.sql takes from this logic
-- (it drives the category-exclusion bypass, the bucket choice and the
-- wireless gate). So if no description changes its flag, every figure
-- the script produces is unchanged. This scans the whole table with no
-- exclusions applied, because is_hw affects which rows get excluded.
-- =====================================================================
WITH old_hw AS (
  -- matched against lower(trim(detail_description)), as telus.sql did before
  SELECT unnest(ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay. canc.',
    'device discount repay. - cr',
    'monthly easy payment',
    'telus easy payment balance',
    'equipment adjustment'
  ]::text[]) AS detail_d
),
new_hw AS (
  -- the same eight as word signatures, matched against norm_detail
  SELECT unnest(ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay canc',
    'device discount repay cr',
    'monthly easy payment',
    'telus easy payment balance',
    'equipment adjustment'
  ]::text[]) AS detail_d
),
base AS (
  SELECT
    r.detail_description,
    r.amount,
    LOWER(TRIM(r.detail_description)) AS detail_d,
    BTRIM(regexp_replace(
      regexp_replace(
        regexp_replace(LOWER(COALESCE(r.detail_description, '')), '\(.*?\)', ' ', 'g'),
        '\(.*$', ' '),
      '[^a-z]+', ' ', 'g')) AS norm_detail
  FROM raw_data.raw_telus_spend AS r
),
flagged AS (
  SELECT
    b.detail_description,
    b.norm_detail,
    b.amount,
    EXISTS (SELECT 1 FROM old_hw h WHERE h.detail_d = b.detail_d)    AS hardware_before,
    EXISTS (SELECT 1 FROM new_hw h WHERE h.detail_d = b.norm_detail) AS hardware_after
  FROM base b
)
SELECT
  detail_description,
  norm_detail,
  hardware_before,
  hardware_after,
  COUNT(*)                          AS row_count,
  ROUND(SUM(amount)::numeric, 2)    AS amount_sum
FROM flagged
WHERE hardware_before <> hardware_after
GROUP BY 1, 2, 3, 4
ORDER BY amount_sum DESC NULLS LAST;


-- =====================================================================
-- QUERY 2 -- What do the seven new families move, and to where?
-- ---------------------------------------------------------------------
-- Runs the full telus.sql pipeline twice -- once with the original eight
-- signatures, once with all fourteen -- and reports the bucket totals
-- side by side per month.
--
-- normalization_and_old_list  = figures as the script produced them before
-- with_new_families           = figures the script produces now
-- Also watch dropped_amount: a new-family row that is neither
-- source='Wireless' nor source_id=164 is removed from every bucket by the
-- wireless gate, so it leaves the report entirely rather than moving.
-- =====================================================================
WITH hw_orig AS (
  SELECT unnest(ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay canc',
    'device discount repay cr',
    'monthly easy payment',
    'telus easy payment balance',
    'equipment adjustment'
  ]::text[]) AS detail_d
),
hw_added AS (
  SELECT unnest(ARRAY[
    'gobc mos easy payment fee',
    'gobc data device pom',
    'office phone device down payment',
    'smb hardware purchase',
    'easy payment yrs',
    'device care complete'
  ]::text[]) AS detail_d
),
excl_category AS (
  SELECT unnest(ARRAY[
    'payment', 'payments', 'amount due from last bill', 'taxes'
  ]::text[]) AS stmt_cat
),
excl_detail AS (
  SELECT unnest(ARRAY[
    'bc pst', 'b.c. pst adjustment', 'bus. services gst', 'cps gst 100652692',
    'cps gst adjustment 362037', 'cps pst british columbia 7%', 'fp gst credit',
    'fp pst credit', 'gst', 'gst adj', 'gst adjustment', 'gst/hst',
    'gst/hst adjustment', 'gst tax adjustment', 'pq pst', 'pst', 'pst adjustment',
    'pst-bc', 'pst-bc adj', 'pst-mb', 'pst-qc'
  ]::text[]) AS detail_d
),
base AS (
  SELECT
    r.amount,
    date_trunc('month', r.statement_date)::date AS month_start,
    LOWER(TRIM(COALESCE(r.statement_category, ''))) AS stmt_cat,
    TRIM(COALESCE(r.source_id::text, '')) AS sid_raw,
    TRIM(LOWER(COALESCE(r.source, ''))) = 'wireless' AS is_wireless,
    BTRIM(regexp_replace(
      regexp_replace(
        regexp_replace(LOWER(COALESCE(r.detail_description, '')), '\(.*?\)', ' ', 'g'),
        '\(.*$', ' '),
      '[^a-z]+', ' ', 'g')) AS norm_detail
  FROM raw_data.raw_telus_spend AS r
  WHERE (LOWER(TRIM(r.detail_description)) NOT IN (SELECT ed.detail_d FROM excl_detail ed)
     OR r.detail_description IS NULL)
    AND COALESCE(LOWER(TRIM(r.statement_section)), '') <> 'balance forward'
),
flags AS (
  SELECT
    b.*,
    EXISTS (SELECT 1 FROM hw_orig h WHERE h.detail_d = b.norm_detail) AS hw_before,
    EXISTS (SELECT 1 FROM hw_orig h WHERE h.detail_d = b.norm_detail)
      OR EXISTS (SELECT 1 FROM hw_added h WHERE h.detail_d = b.norm_detail) AS hw_after,
    CASE
      WHEN b.sid_raw ~ '^-?[0-9]+(\.[0-9]+)?$' THEN (b.sid_raw::numeric)::bigint::text
      WHEN b.sid_raw = '' THEN NULL
      ELSE b.sid_raw
    END AS sid_n
  FROM base b
),
-- Same row evaluated under both hardware lists.
expanded AS (
  SELECT
    v.variant,
    f.month_start,
    f.amount,
    f.stmt_cat,
    f.sid_n,
    f.is_wireless,
    CASE v.variant WHEN 'before' THEN f.hw_before ELSE f.hw_after END AS is_hw
  FROM flags f
  CROSS JOIN (VALUES ('before'), ('after')) AS v(variant)
),
-- Identical bucketing rules to telus.sql.
bucketed AS (
  SELECT
    variant,
    month_start,
    amount,
    CASE
      WHEN is_hw OR sid_n = '164' THEN 'cellular_hardware'
      WHEN sid_n = '130' OR is_wireless THEN 'cellular_plans'
      WHEN sid_n IN ('1001', '103') THEN 'data'
      WHEN sid_n IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM expanded
  WHERE (is_hw OR stmt_cat NOT IN (SELECT x.stmt_cat FROM excl_category x))
    AND month_start IS NOT NULL
    AND (NOT is_hw OR is_wireless OR sid_n = '164')
),
-- Rows the wireless gate removes entirely once the new families count as hardware.
dropped AS (
  SELECT
    month_start,
    ROUND(SUM(amount)::numeric, 2) AS dropped_amount,
    COUNT(*) AS dropped_rows
  FROM flags
  WHERE hw_after AND NOT hw_before
    AND NOT is_wireless
    AND COALESCE(sid_n, '') <> '164'
    AND month_start IS NOT NULL
    AND (hw_before OR stmt_cat NOT IN (SELECT x.stmt_cat FROM excl_category x))
  GROUP BY 1
),
totals AS (
  SELECT
    month_start,
    bucket,
    ROUND(SUM(amount) FILTER (WHERE variant = 'before')::numeric, 2) AS amount_before,
    ROUND(SUM(amount) FILTER (WHERE variant = 'after')::numeric, 2)  AS amount_after
  FROM bucketed
  GROUP BY 1, 2
)
SELECT
  t.month_start,
  t.bucket,
  COALESCE(t.amount_before, 0) AS amount_before,
  COALESCE(t.amount_after, 0)  AS amount_after,
  COALESCE(t.amount_after, 0) - COALESCE(t.amount_before, 0) AS difference,
  -- per month, not per bucket: shown once, on the cellular_hardware row
  CASE WHEN t.bucket = 'cellular_hardware' THEN d.dropped_amount END AS dropped_amount,
  CASE WHEN t.bucket = 'cellular_hardware' THEN d.dropped_rows   END AS dropped_rows
FROM totals t
LEFT JOIN dropped d ON d.month_start = t.month_start
ORDER BY t.month_start, t.bucket;
