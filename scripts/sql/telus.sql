WITH hw_detail AS (
  SELECT unnest(ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay. canc.',
    'device discount repay. - cr',
    'monthly easy payment',
	'telus easy payment balance',
	'equipment adjustment'
  ]::text[]) AS detail_d
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
    LOWER(TRIM(r.detail_description)) AS detail_d,
    LOWER(TRIM(COALESCE(r.statement_category, ''))) AS stmt_cat,
    TRIM(COALESCE(r.source_id::text, '')) AS sid_raw,
    EXISTS (SELECT 1 FROM hw_detail h WHERE h.detail_d = LOWER(TRIM(r.detail_description))) AS is_hw,
    TRIM(LOWER(COALESCE(r.source, ''))) = 'wireless' AS is_wireless
  FROM raw_data.raw_telus_spend AS r
  WHERE (LOWER(TRIM(r.detail_description)) NOT IN (SELECT ed.detail_d FROM excl_detail ed)
     OR r.detail_description IS NULL)
    AND COALESCE(LOWER(TRIM(r.statement_section)), '') <> 'balance forward'
),
flagged AS (
  SELECT
    sheet_name,
    month_start,
    amount,
    is_hw,
    is_wireless,
    CASE
      WHEN is_hw
        OR stmt_cat NOT IN (SELECT x.stmt_cat FROM excl_category x)
      THEN TRUE
      ELSE FALSE
    END AS is_included,
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
      WHEN is_hw THEN 'cellular_hardware'
      WHEN sid_n IN ('164','130') OR is_wireless THEN 'cellular_plans'
      WHEN sid_n IN ('1001', '103') THEN 'data'
      WHEN sid_n IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM flagged
  WHERE is_included
    AND month_start IS NOT NULL
    AND (NOT is_hw OR is_wireless)
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
