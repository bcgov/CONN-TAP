-- Data (source_id = 103): NG-prefix match rate and text-fallback methods.
-- Expected: ~96.6% match via NG##### → raw_telus_data_services_pricebook.service_id

WITH spend AS (
  SELECT
    raw_id,
    amount,
    TRIM(detail_description) AS detail_d,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[0-9]{5})')) AS ng_id,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source_id) = '103'
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
    )
    AND COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
),
classified AS (
  SELECT
    s.*,
    CASE
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_data_services_pricebook d
        WHERE UPPER(TRIM(d.service_id)) = s.ng_id
      ) THEN 'ng_id'
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_data_services_pricebook d
        WHERE LOWER(TRIM(REGEXP_REPLACE(d.short_service_description, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
          OR LOWER(TRIM(REGEXP_REPLACE(d.service_name, '[^a-z0-9 ]', '', 'g'))) = s.norm_detail
      ) THEN 'text_exact'
      WHEN EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_data_services_pricebook d
        WHERE LENGTH(s.norm_detail) > 8
          AND (
            POSITION(
              LOWER(TRIM(REGEXP_REPLACE(d.short_service_description, '[^a-z0-9 ]', '', 'g')))
              IN s.norm_detail
            ) > 0
            OR POSITION(s.norm_detail IN LOWER(TRIM(REGEXP_REPLACE(d.short_service_description, '[^a-z0-9 ]', '', 'g')))) > 0
          )
      ) THEN 'text_partial'
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

-- NG codes in data spend: top by row count with pricebook confirmation
SELECT
  UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[0-9]{5})')) AS ng_code,
  TRIM(source_id) AS source_id,
  COUNT(*) AS row_count,
  d.service_id AS data_pb_match,
  v.service_id AS voice_pb_match
FROM raw_data.raw_telus_spend s
LEFT JOIN raw_data.raw_telus_data_services_pricebook d
  ON UPPER(TRIM(d.service_id)) = UPPER(SUBSTRING(TRIM(s.detail_description) FROM '^(NG[0-9]{5})'))
LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
  ON UPPER(TRIM(v.service_id)) = UPPER(SUBSTRING(TRIM(s.detail_description) FROM '^(NG[0-9]{5})'))
WHERE TRIM(s.detail_description) ~ '^NG[0-9]{5}'
GROUP BY 1, 2, 4, 5
ORDER BY row_count DESC
LIMIT 30;
