-- Voice recurring (source_id = 102): match method breakdown.
-- NG code: UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})'))

WITH spend AS (
  SELECT
    raw_id,
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
classified AS (
  SELECT
    s.*,
    CASE
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_voice_services_pricebook v
        WHERE UPPER(TRIM(v.service_id)) = s.ng_id
      ) THEN 'voice_ng_id'
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_data_services_pricebook d
        WHERE UPPER(TRIM(d.service_id)) = s.ng_id
      ) THEN 'data_ng_id_misclass'
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_voice_services_pricebook v
        WHERE LOWER(TRIM(REGEXP_REPLACE(v.short_service_description, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
      ) THEN 'voice_text'
      ELSE 'unmatched'
    END AS match_method
  FROM spend s
)
SELECT
  match_method,
  COUNT(*) AS row_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_rows,
  ROUND(SUM(amount)::numeric, 0) AS total_amount
FROM classified
GROUP BY 1
ORDER BY row_count DESC;

-- Top recurring voice detail_descriptions with pricebook lookup
SELECT
  TRIM(detail_description) AS detail_d,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount,
  v.service_id AS voice_pb_id,
  LEFT(v.short_service_description, 60) AS voice_short_desc
FROM raw_data.raw_telus_spend s
LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
  ON UPPER(TRIM(v.service_id)) = UPPER(SUBSTRING(TRIM(s.detail_description) FROM '^(NG[A-Z0-9]{2,6})'))
WHERE TRIM(s.source_id) = '102'
  AND TRIM(COALESCE(s.statement_category, '')) = 'Recurring Service Charges'
  AND TRIM(s.detail_description) ~ '^(NG|PRI|CENTREX|BUSINESS|IP TRUNKING|WAVELENGTH)'
GROUP BY 1, 4, 5
ORDER BY row_count DESC
LIMIT 25;

-- Voice spend by statement_category
SELECT
  TRIM(statement_category) AS statement_category,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 0) AS total_amount,
  COUNT(*) FILTER (WHERE TRIM(detail_description) ~ '^NG') AS ng_prefix_rows
FROM raw_data.raw_telus_spend
WHERE TRIM(source_id) = '102'
GROUP BY 1
ORDER BY total_amount DESC NULLS LAST;
