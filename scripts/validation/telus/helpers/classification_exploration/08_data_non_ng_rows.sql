-- Data rows (source_id = 103) without NG##### prefix in detail_description.

SELECT
  TRIM(COALESCE(statement_category, '')) AS statement_category,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 0) AS total_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(source_id) = '103'
  AND (TRIM(detail_description) IS NULL OR TRIM(detail_description) !~ '^NG[0-9]{5}')
  AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN ('taxes', 'payment', 'payments')
GROUP BY 1
ORDER BY total_amount DESC NULLS LAST;

-- Top non-NG detail_descriptions by amount (excl. amount due from last bill)
SELECT
  TRIM(detail_description) AS detail_d,
  TRIM(service_description) AS service_d,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(source_id) = '103'
  AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
    'taxes', 'payment', 'payments', 'amount due from last bill'
  )
  AND (TRIM(detail_description) IS NULL OR TRIM(detail_description) !~ '^NG[0-9]{5}')
GROUP BY 1, 2
ORDER BY total_amount DESC NULLS LAST
LIMIT 20;

-- Non-NG recurring: exact/partial text match to data pricebook
WITH spend AS (
  SELECT
    raw_id,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source_id) = '103'
    AND COALESCE(LOWER(TRIM(statement_category)), '') = 'recurring service charges'
    AND (TRIM(detail_description) IS NULL OR TRIM(detail_description) !~ '^NG[0-9]{5}')
),
pb AS (
  SELECT
    LOWER(TRIM(REGEXP_REPLACE(short_service_description, '[^a-z0-9 ]', '', 'g'))) AS norm_desc,
    LOWER(TRIM(REGEXP_REPLACE(service_name, '[^a-z0-9 ]', '', 'g'))) AS norm_name
  FROM raw_data.raw_telus_data_services_pricebook
)
SELECT
  COUNT(*) AS total_non_ng_recurring,
  COUNT(*) FILTER (
    WHERE EXISTS (
      SELECT 1 FROM pb WHERE pb.norm_desc = s.norm_detail OR pb.norm_name = s.norm_detail
    )
  ) AS exact_norm_match,
  COUNT(*) FILTER (
    WHERE EXISTS (
      SELECT 1 FROM pb
      WHERE POSITION(pb.norm_desc IN s.norm_detail) > 0
         OR POSITION(s.norm_detail IN pb.norm_desc) > 0
    )
  ) AS partial_match
FROM spend s;
