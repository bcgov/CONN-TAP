-- Wireline: NG-code pricebook bucket vs current source_id bucket.
-- Uses NG[A-Z0-9]{2,6} prefix; data pricebook checked before voice.

WITH spend AS (
  SELECT
    raw_id,
    amount,
    TRIM(source) AS source,
    TRIM(source_id) AS source_id,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})')) AS ng_id
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source) = 'Wireline'
    AND TRIM(source_id) IN ('102', '103', '104', '106')
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
    )
),
with_pb AS (
  SELECT
    s.*,
    CASE
      WHEN TRIM(s.source_id) = '103' THEN 'data_sid'
      WHEN TRIM(s.source_id) IN ('102', '104', '106') THEN 'voice_sid'
    END AS source_id_bucket,
    CASE
      WHEN d.service_id IS NOT NULL THEN 'data_pb'
      WHEN v.service_id IS NOT NULL THEN 'voice_pb'
      ELSE 'no_pb'
    END AS pricebook_bucket
  FROM spend s
  LEFT JOIN raw_data.raw_telus_data_services_pricebook d
    ON UPPER(TRIM(d.service_id)) = s.ng_id
  LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
    ON UPPER(TRIM(v.service_id)) = s.ng_id
    AND d.service_id IS NULL
)
SELECT
  source_id_bucket,
  pricebook_bucket,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 0) AS total_amount
FROM with_pb
GROUP BY 1, 2
ORDER BY 1, total_amount DESC NULLS LAST;

-- service_description usefulness for data rows
SELECT
  COUNT(*) FILTER (WHERE TRIM(COALESCE(service_description, '')) ~ 'CSID') AS has_csid,
  COUNT(*) FILTER (WHERE TRIM(COALESCE(service_description, '')) ~ 'NG[0-9]{5}') AS has_ng_in_service_desc,
  COUNT(*) AS total_rows
FROM raw_data.raw_telus_spend
WHERE TRIM(source_id) = '103';
