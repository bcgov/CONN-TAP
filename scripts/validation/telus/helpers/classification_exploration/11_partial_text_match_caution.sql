-- CAUTION: SLOW. Demonstrates inflated voice→data reclassification from
-- POSITION(short_service_description IN detail_description) partial matching.
-- Do NOT use the amt_reclass_to_data figure for implementation (~$18M is false positives).
-- See scripts/sql/telus_classification.md § "Do not use broad POSITION".

WITH spend AS (
  SELECT
    raw_id,
    amount,
    LOWER(TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(detail_description, '\*', '', 'g'),
      '[^a-z0-9 ]', '', 'g'
    ))) AS norm_detail
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source_id) IN ('102', '104', '106')
    AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges'
),
pb_data AS (
  SELECT
    service_id,
    LOWER(TRIM(REGEXP_REPLACE(short_service_description, '[^a-z0-9 ]', '', 'g'))) AS norm_desc
  FROM raw_data.raw_telus_data_services_pricebook
),
pb_voice AS (
  SELECT
    service_id,
    LOWER(TRIM(REGEXP_REPLACE(short_service_description, '[^a-z0-9 ]', '', 'g'))) AS norm_desc
  FROM raw_data.raw_telus_voice_services_pricebook
),
matched AS (
  SELECT
    s.raw_id,
    s.amount,
    vd.service_id AS voice_match,
    dd.service_id AS data_match
  FROM spend s
  LEFT JOIN pb_voice vd ON vd.norm_desc = s.norm_detail
  LEFT JOIN pb_data dd ON (
    dd.norm_desc = s.norm_detail
    OR POSITION(dd.norm_desc IN s.norm_detail) > 0
  )
)
SELECT
  COUNT(*) FILTER (WHERE voice_match IS NULL AND data_match IS NOT NULL) AS voice_sid_data_text_only,
  ROUND(SUM(amount) FILTER (WHERE voice_match IS NULL AND data_match IS NOT NULL)::numeric, 0) AS amt_reclass_to_data,
  COUNT(*) FILTER (WHERE voice_match IS NOT NULL) AS voice_sid_voice_match,
  COUNT(*) FILTER (WHERE voice_match IS NULL AND data_match IS NULL) AS no_match
FROM matched;
