-- Voice recurring (source_id = 102) with no pricebook match: top by amount.

WITH spend AS (
  SELECT
    TRIM(detail_description) AS detail_d,
    amount,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})')) AS ng_id,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source_id) = '102'
    AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges'
),
unmatched AS (
  SELECT s.*
  FROM spend s
  WHERE NOT EXISTS (
    SELECT 1
    FROM raw_data.raw_telus_voice_services_pricebook v
    WHERE UPPER(TRIM(v.service_id)) = s.ng_id
  )
  AND NOT EXISTS (
    SELECT 1
    FROM raw_data.raw_telus_data_services_pricebook d
    WHERE UPPER(TRIM(d.service_id)) = s.ng_id
  )
  AND NOT EXISTS (
    SELECT 1
    FROM raw_data.raw_telus_voice_services_pricebook v
    WHERE LOWER(TRIM(REGEXP_REPLACE(v.short_service_description, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
  )
)
SELECT
  detail_d,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM unmatched
GROUP BY 1
HAVING SUM(amount) > 500
ORDER BY total_amount DESC
LIMIT 20;

-- Non-NG recurring voice: exact short_service_description match coverage
WITH spend AS (
  SELECT
    TRIM(detail_description) AS detail_d,
    amount,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source_id) = '102'
    AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges'
    AND (TRIM(detail_description) IS NULL OR TRIM(detail_description) !~ '^NG')
),
pb AS (
  SELECT
    service_id,
    LOWER(TRIM(REGEXP_REPLACE(short_service_description, '[^a-z0-9 ]', '', 'g'))) AS norm_desc
  FROM raw_data.raw_telus_voice_services_pricebook
)
SELECT
  COUNT(DISTINCT s.detail_d) AS distinct_detail_values,
  COUNT(DISTINCT s.detail_d) FILTER (WHERE p.service_id IS NOT NULL) AS matched_distinct_values,
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE p.service_id IS NOT NULL) AS matched_rows,
  ROUND(SUM(s.amount) FILTER (WHERE p.service_id IS NOT NULL)::numeric, 0) AS matched_amount,
  ROUND(SUM(s.amount)::numeric, 0) AS total_amount
FROM spend s
LEFT JOIN pb p ON p.norm_desc = s.norm_detail;
