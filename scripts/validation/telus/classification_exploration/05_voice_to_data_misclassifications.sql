-- Voice source_id rows that match the DATA pricebook (misclassifications).
-- Expected total: ~119 rows / (NGFIB*, WAVELENGTH*, NG WAN L1 WAVE*).

-- Cross-bucket: voice source_id bucket but NG code hits data pricebook
WITH classified AS (
  SELECT
    raw_id,
    amount,
    TRIM(source) AS source,
    TRIM(source_id) AS source_id,
    TRIM(detail_description) AS detail_d,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})')) AS ng_id,
    CASE
      WHEN TRIM(source) = 'Wireless' OR TRIM(source_id) IN ('164', '130') THEN 'cellular_plans'
      WHEN TRIM(source_id) IN ('1001', '103') THEN 'data'
      WHEN TRIM(source_id) IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS source_id_bucket
  FROM raw_data.raw_telus_spend
  WHERE COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
    )
),
with_pb AS (
  SELECT
    c.*,
    CASE
      WHEN d.service_id IS NOT NULL THEN 'data'
      WHEN v.service_id IS NOT NULL THEN 'voice'
    END AS pricebook_bucket,
    d.service_name AS data_service_name
  FROM classified c
  LEFT JOIN raw_data.raw_telus_data_services_pricebook d
    ON UPPER(TRIM(d.service_id)) = c.ng_id
  LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
    ON UPPER(TRIM(v.service_id)) = c.ng_id
    AND d.service_id IS NULL
)
SELECT
  source_id_bucket,
  pricebook_bucket,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 0) AS total_amount
FROM with_pb
WHERE ng_id IS NOT NULL
  AND pricebook_bucket IS NOT NULL
  AND source_id_bucket <> pricebook_bucket
GROUP BY 1, 2
ORDER BY row_count DESC;

-- Detail: voice source_id rows matching data pricebook by NG code
WITH classified AS (
  SELECT
    raw_id,
    amount,
    TRIM(source) AS source,
    TRIM(source_id) AS source_id,
    TRIM(detail_description) AS detail_d,
    UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})')) AS ng_id,
    CASE
      WHEN TRIM(source) = 'Wireless' OR TRIM(source_id) IN ('164', '130') THEN 'cellular_plans'
      WHEN TRIM(source_id) IN ('1001', '103') THEN 'data'
      WHEN TRIM(source_id) IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS source_id_bucket
  FROM raw_data.raw_telus_spend
  WHERE COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
    AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill'
    )
),
with_pb AS (
  SELECT
    c.*,
    CASE
      WHEN d.service_id IS NOT NULL THEN 'data'
      WHEN v.service_id IS NOT NULL THEN 'voice'
    END AS pricebook_bucket,
    d.service_name AS data_service_name
  FROM classified c
  LEFT JOIN raw_data.raw_telus_data_services_pricebook d
    ON UPPER(TRIM(d.service_id)) = c.ng_id
  LEFT JOIN raw_data.raw_telus_voice_services_pricebook v
    ON UPPER(TRIM(v.service_id)) = c.ng_id
    AND d.service_id IS NULL
)
SELECT
  detail_d,
  source,
  source_id,
  ng_id,
  data_service_name,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM with_pb
WHERE source_id_bucket = 'voice'
  AND pricebook_bucket = 'data'
GROUP BY 1, 2, 3, 4, 5
ORDER BY total_amount DESC;

-- Wavelength / fibre rows (known misclassifications)
SELECT
  TRIM(detail_description) AS detail_d,
  TRIM(source_id) AS source_id,
  TRIM(source) AS source,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(detail_description) ILIKE '%wavelength%'
   OR TRIM(detail_description) ILIKE '%WAN L1 WAVE%'
   OR TRIM(detail_description) ~ '^NGFIB'
GROUP BY 1, 2, 3
ORDER BY total_amount DESC;

-- Data pricebook entries for NGFIB / wavelength
SELECT service_id, service_name, short_service_description
FROM raw_data.raw_telus_data_services_pricebook
WHERE service_id LIKE 'NGFIB%'
   OR short_service_description ILIKE '%wave%'
ORDER BY service_id;
