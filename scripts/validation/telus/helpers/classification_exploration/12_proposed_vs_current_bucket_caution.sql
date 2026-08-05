-- CAUTION: VERY SLOW. Full proposed logic vs current source_id bucket.
-- Includes flawed POSITION partial text match — inflates voice→data delta (~702k rows / ~$6.3M).
-- NG-code-only reclassification is ~119 rows / ~$228k (see 05_voice_to_data_misclassifications.sql).
-- See scripts/sql/telus_classification.md § "Full proposed logic vs current bucket".

WITH spend AS (
  SELECT
    raw_id,
    amount,
    TRIM(source) AS source,
    TRIM(source_id) AS source_id,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})')) AS ng_id,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
    AND LOWER(TRIM(COALESCE(detail_description, ''))) NOT IN (
      'hardware purchase charge', 'device discount repayment',
      'monthly telus easy payment', 'device discount repay. canc.',
      'device discount repay. - cr', 'monthly easy payment',
      'telus easy payment balance', 'equipment adjustment'
    )
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
    )
),
pb_bucket AS (
  SELECT
    s.raw_id,
    CASE
      WHEN s.source = 'Wireless' OR s.source_id IN ('164', '130') THEN 'cellular_plans'
      WHEN d.service_id IS NOT NULL THEN 'data'
      WHEN v.service_id IS NOT NULL THEN 'voice'
      WHEN dd.service_id IS NOT NULL THEN 'data'
      WHEN vd.service_id IS NOT NULL THEN 'voice'
      WHEN s.source_id IN ('1001', '103') THEN 'data'
      WHEN s.source_id IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS proposed_bucket
  FROM spend s
  LEFT JOIN raw_data.raw_telus_data_services_pricebook d
    ON UPPER(TRIM(d.service_id)) = s.ng_id
  LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
    ON UPPER(TRIM(v.service_id)) = s.ng_id
    AND d.service_id IS NULL
  LEFT JOIN raw_data.raw_telus_data_services_pricebook dd ON (
    LOWER(TRIM(REGEXP_REPLACE(dd.short_service_description, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
    OR (
      LENGTH(s.norm_detail) > 10
      AND POSITION(
        LOWER(TRIM(REGEXP_REPLACE(dd.short_service_description, '[^a-z0-9 ]', '', 'g')))
        IN s.norm_detail
      ) > 0
    )
  )
  LEFT JOIN raw_data.raw_telus_voice_services_pricebook vd ON (
    LOWER(TRIM(REGEXP_REPLACE(vd.short_service_description, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
  )
),
current_bucket AS (
  SELECT
    raw_id,
    CASE
      WHEN source = 'Wireless' OR source_id IN ('164', '130') THEN 'cellular_plans'
      WHEN source_id IN ('1001', '103') THEN 'data'
      WHEN source_id IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS current_bucket
  FROM spend
),
deduped_proposed AS (
  SELECT DISTINCT ON (raw_id)
    raw_id,
    proposed_bucket
  FROM pb_bucket
  ORDER BY raw_id, proposed_bucket
)
SELECT
  c.current_bucket,
  p.proposed_bucket,
  COUNT(*) AS row_count,
  ROUND(SUM(s.amount)::numeric, 0) AS total_amount
FROM spend s
JOIN current_bucket c ON c.raw_id = s.raw_id
JOIN deduped_proposed p ON p.raw_id = s.raw_id
WHERE c.current_bucket IN ('cellular_plans', 'data', 'voice')
  AND c.current_bucket <> p.proposed_bucket
GROUP BY 1, 2
ORDER BY total_amount DESC;
