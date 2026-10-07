-- Requires the current dbt seed; hardware patterns are shared with the validators.
WITH hw_detail AS (
  SELECT LOWER(TRIM(detail_description)) AS detail_d
  FROM seeds.telus_hardware_details
),
excl_category AS (
  SELECT unnest(ARRAY[
    'payment',
    'payments',
    'amount due from last bill',
    'taxes'
  ]::text[]) AS stmt_cat
),
excl_detail AS (
  SELECT unnest(ARRAY[
    'bc pst',
    'b.c. pst adjustment',
    'bus. services gst',
    'cps gst 100652692',
    'cps gst adjustment 362037',
    'cps pst british columbia 7%',
    'fp gst credit',
    'fp pst credit',
    'gst',
    'gst adj',
    'gst adjustment',
    'gst/hst',
    'gst/hst adjustment',
    'gst tax adjustment',
    'pq pst',
    'pst',
    'pst adjustment',
    'pst-bc',
    'pst-bc adj',
    'pst-mb',
    'pst-qc'
  ]::text[]) AS detail_d
),
src AS (
  SELECT
    r.sheet_name,
    r.amount,
    date_trunc('month', r.statement_date)::date AS month_start,
    TRIM(COALESCE(r.source_id::text, '')) AS sid_raw,
    EXISTS (SELECT 1 FROM hw_detail h WHERE LOWER(TRIM(r.detail_description)) LIKE h.detail_d) AS is_hw,
    TRIM(LOWER(COALESCE(r.source, ''))) = 'wireless' AS is_wireless
  FROM raw_data.raw_telus_spend AS r
  WHERE (LOWER(TRIM(r.detail_description)) NOT IN (SELECT ed.detail_d FROM excl_detail ed)
     OR r.detail_description IS NULL)
    AND COALESCE(LOWER(TRIM(r.statement_section)), '') <> 'balance forward'
    -- Exclusions apply before classification, including to hardware and source_id 164.
    AND COALESCE(LOWER(TRIM(r.statement_category)), '') NOT IN (
      SELECT x.stmt_cat FROM excl_category x
    )
    AND r.statement_date IS NOT NULL
),
normalized AS (
  SELECT
    sheet_name,
    month_start,
    amount,
    is_hw,
    is_wireless,
    CASE
      WHEN sid_raw ~ '^-?[0-9]+(\.[0-9]+)?$'
        THEN (sid_raw::numeric)::bigint::text
      WHEN sid_raw = '' THEN NULL
      ELSE sid_raw
    END AS sid_n
  FROM src
),
bucketed AS (
  SELECT
    sheet_name,
    month_start,
    amount,
    CASE
      WHEN is_hw OR sid_n = '164' THEN 'cellular_hardware'
      WHEN sid_n = '130' OR is_wireless THEN 'cellular_plans'
      WHEN sid_n IN ('1001', '103') THEN 'data'
      WHEN sid_n IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM normalized
  -- 'Onetime' isn't a safe signal on its own (it covers non-cellular one-time
  -- charges too); a hardware-detail-text row is only trusted as cellular
  -- hardware if it's wireless-plan-sourced or explicitly source_id 164.
  WHERE NOT is_hw OR is_wireless OR sid_n = '164'
)
SELECT
  'telus'::text AS provider,
  sheet_name AS entity_key,
  month_start,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_hardware'), 0) AS cellular_hardware,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_plans'), 0)   AS cellular_plans,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'data'), 0)             AS data_spend,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'voice'), 0)            AS voice_spend,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'other'), 0)            AS other_spend,
  COALESCE(SUM(amount), 0) AS total_reported
FROM bucketed
GROUP BY sheet_name, month_start
ORDER BY month_start, sheet_name;
