-- Wireless (source = Wireless, source_id = 130): GoBC plan name → cellular pricebook service_id.
-- Positive recurring service charges only.

WITH plans AS (
  SELECT
    raw_id,
    amount,
    TRIM(detail_description) AS detail_d,
    CASE
      WHEN detail_description ~* 'GoBC V&D ULNA [0-9]+GB' THEN
        'XPULNA'
        || REGEXP_REPLACE(detail_description, '.*V&D ULNA ([0-9]+)GB.*', '\1', 'i')
        || CASE
          WHEN REGEXP_REPLACE(detail_description, '.*V&D ULNA ([0-9]+)GB.*', '\1', 'i')
            IN ('1', '2', '3', '4', '5', '6', '7', '8', '9') THEN 'GB'
          ELSE 'G'
        END
      WHEN detail_description ILIKE 'GoBC Data 5GB%' THEN 'XPTMHS5GB'
      WHEN detail_description ILIKE 'GoBC Data 10GB%' THEN 'XPTMHS10G'
      WHEN detail_description ILIKE 'GoBC Voice ULNA%' THEN 'XPULNAV01'
      WHEN detail_description ILIKE '%High Capacity Data 500GB%' THEN 'XPDAT500G'
      WHEN detail_description ILIKE '%High Capacity Data 100GB%' THEN 'XPDAT100G'
      WHEN detail_description ILIKE '%High Capacity Data Access%'
        OR detail_description ILIKE 'TSMA Data Access%' THEN 'XPHCDATAC'
      WHEN detail_description ILIKE '%Public Static IP%' THEN 'XSNGTASIP'
      WHEN detail_description ILIKE '%Visual Voicemail%' THEN 'XSNGTAVVM'
      WHEN detail_description ILIKE '%Network Priority%' THEN 'XSNGTAPRI'
      WHEN detail_description ILIKE '%Vacation Disconnect%' THEN 'XPVAD5'
    END AS mapped_service_id
  FROM raw_data.raw_telus_spend
  WHERE TRIM(source) = 'Wireless'
    AND TRIM(source_id) = '130'
    AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges'
    AND amount > 0
)
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE mapped_service_id IS NOT NULL) AS mapped_rows,
  COUNT(*) FILTER (
    WHERE mapped_service_id IS NOT NULL
      AND EXISTS (
        SELECT 1
        FROM raw_data.raw_telus_cellular_services_pricebook p
        WHERE TRIM(p.service_id) = plans.mapped_service_id
        UNION ALL
        SELECT 1
        FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook p
        WHERE TRIM(p.service_id) = plans.mapped_service_id
        UNION ALL
        SELECT 1
        FROM raw_data.raw_telus_control_center_services_pricebook p
        WHERE TRIM(p.service_id) = plans.mapped_service_id
      )
  ) AS mapped_in_pricebook,
  ROUND(SUM(amount) FILTER (WHERE mapped_service_id IS NOT NULL)::numeric, 0) AS mapped_amount,
  ROUND(SUM(amount)::numeric, 0) AS total_amount
FROM plans;

-- Top positive recurring wireless plan names by amount
SELECT
  TRIM(detail_description) AS detail_d,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(source) = 'Wireless'
  AND TRIM(source_id) = '130'
  AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges'
  AND amount > 0
  AND TRIM(COALESCE(detail_description, '')) NOT IN ('', 'Service')
GROUP BY 1
ORDER BY total_amount DESC
LIMIT 25;

-- Quick coverage: rows matching GoBC/TSMA-style name patterns
SELECT
  COUNT(*) FILTER (WHERE amount > 0) AS positive_rows,
  COUNT(*) FILTER (
    WHERE amount > 0
      AND detail_description ~* 'GoBC|TSMA|Corp Vacation|Visual Voicemail|Static IP|Network Priority|High Capacity'
  ) AS name_pattern_rows,
  ROUND(SUM(amount) FILTER (WHERE amount > 0)::numeric, 0) AS positive_amount,
  ROUND(SUM(amount) FILTER (
    WHERE amount > 0
      AND detail_description ~* 'GoBC|TSMA|Corp Vacation|Visual Voicemail|Static IP|Network Priority|High Capacity'
  )::numeric, 0) AS name_pattern_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(source) = 'Wireless'
  AND TRIM(source_id) = '130'
  AND TRIM(COALESCE(statement_category, '')) = 'Recurring Service Charges';
