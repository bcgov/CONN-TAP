-- CAUTION: SLOW. Full table scan with fuzzy pricebook join.
-- Illustrates why broad substring matching fails for cellular_plans (false voice matches).
-- See scripts/sql/telus_classification.md § "Fuzzy pricebook matching does not work for cellular".

WITH pb AS (
  SELECT 'cellular_plans' AS bucket, LOWER(TRIM(service_id)) AS key
  FROM raw_data.raw_telus_cellular_services_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'cellular_plans', LOWER(TRIM(rate_plan))
  FROM raw_data.raw_telus_cellular_services_pricebook
  WHERE rate_plan IS NOT NULL
  UNION ALL
  SELECT 'cellular_plans', LOWER(TRIM(service_id))
  FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'cellular_plans', LOWER(TRIM(service_id))
  FROM raw_data.raw_telus_cellular_mms_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'cellular_plans', LOWER(TRIM(service_id))
  FROM raw_data.raw_telus_control_center_services_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'data', LOWER(TRIM(service_id))
  FROM raw_data.raw_telus_data_services_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'data', LOWER(TRIM(service_name))
  FROM raw_data.raw_telus_data_services_pricebook
  WHERE service_name IS NOT NULL
  UNION ALL
  SELECT 'data', LOWER(TRIM(short_service_description))
  FROM raw_data.raw_telus_data_services_pricebook
  WHERE short_service_description IS NOT NULL
  UNION ALL
  SELECT 'voice', LOWER(TRIM(service_id))
  FROM raw_data.raw_telus_voice_services_pricebook
  WHERE service_id IS NOT NULL AND TRIM(service_id) <> ''
  UNION ALL
  SELECT 'voice', LOWER(TRIM(service_name))
  FROM raw_data.raw_telus_voice_services_pricebook
  WHERE service_name IS NOT NULL
  UNION ALL
  SELECT 'voice', LOWER(TRIM(short_service_description))
  FROM raw_data.raw_telus_voice_services_pricebook
  WHERE short_service_description IS NOT NULL
),
spend AS (
  SELECT
    raw_id,
    amount,
    TRIM(source) AS source,
    TRIM(source_id) AS source_id,
    LOWER(TRIM(detail_description)) AS detail_d,
    LOWER(TRIM(service_description)) AS service_d
  FROM raw_data.raw_telus_spend
  WHERE COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
    AND LOWER(TRIM(COALESCE(detail_description, ''))) NOT IN (
      'hardware purchase charge', 'device discount repayment',
      'monthly telus easy payment', 'device discount repay. canc.',
      'device discount repay. - cr', 'monthly easy payment',
      'telus easy payment balance', 'equipment adjustment',
      'gst', 'pst', 'pst-bc', 'gst/hst', 'bc pst', 'bus. services gst'
    )
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
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
best_match AS (
  SELECT DISTINCT ON (s.raw_id)
    s.raw_id,
    p.bucket AS pb_bucket
  FROM spend s
  JOIN pb p ON (
    s.detail_d = p.key
    OR s.service_d = p.key
    OR (
      LENGTH(p.key) >= 5
      AND (
        POSITION(p.key IN s.detail_d) > 0
        OR POSITION(p.key IN s.service_d) > 0
      )
    )
  )
  ORDER BY
    s.raw_id,
    CASE
      WHEN s.detail_d = p.key THEN 1
      WHEN s.service_d = p.key THEN 2
      WHEN LENGTH(p.key) >= 5 AND POSITION(p.key IN s.detail_d) > 0 THEN 3
      WHEN LENGTH(p.key) >= 5 AND POSITION(p.key IN s.service_d) > 0 THEN 4
      ELSE 5
    END
)
SELECT
  c.current_bucket,
  COALESCE(b.pb_bucket, 'unmatched') AS pb_bucket,
  COUNT(*) AS row_count,
  ROUND(SUM(s.amount)::numeric, 0) AS total_amount,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY c.current_bucket), 1) AS pct_rows
FROM spend s
JOIN current_bucket c ON c.raw_id = s.raw_id
LEFT JOIN best_match b ON b.raw_id = s.raw_id
WHERE c.current_bucket IN ('cellular_plans', 'data', 'voice')
GROUP BY 1, 2
ORDER BY 1, row_count DESC;
