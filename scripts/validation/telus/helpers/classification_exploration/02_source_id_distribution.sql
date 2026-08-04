-- source / source_id distribution in raw_telus_spend (excl. balance forward).

SELECT
  TRIM(source) AS source,
  CASE
    WHEN TRIM(source_id) ~ '^-?[0-9]+(\.[0-9]+)?$'
      THEN (TRIM(source_id)::numeric)::bigint::text
    ELSE TRIM(source_id)
  END AS source_id,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM raw_data.raw_telus_spend
WHERE COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
GROUP BY 1, 2
ORDER BY row_count DESC;

-- Rows where source is blank but source_id is set
SELECT
  TRIM(COALESCE(source, '')) AS source,
  TRIM(COALESCE(source_id, '')) AS source_id,
  COUNT(*) AS row_count,
  ROUND(SUM(amount)::numeric, 2) AS total_amount
FROM raw_data.raw_telus_spend
WHERE TRIM(COALESCE(source, '')) NOT IN ('Wireless', 'Wireline', 'OneTime')
GROUP BY 1, 2
ORDER BY row_count DESC;
