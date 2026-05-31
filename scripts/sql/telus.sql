WITH hw_detail AS (
  SELECT unnest(ARRAY[
    'Hardware Purchase Charge',
    'Device Discount Repayment',
    'Monthly TELUS Easy Payment',
    'Device discount repay. canc.',
    'Device discount repay. - CR',
    'Monthly Easy Payment',
	'TELUS Easy Payment Balance',
	'Equipment Adjustment'
  ]::text[]) AS detail_d
),
excl_category AS (
  SELECT unnest(ARRAY[
    'Payment',
    'Payments',
    'Amount due from last bill',
    'Amount Due from last bill',
    'Taxes'
  ]::text[]) AS stmt_cat
),
excl_detail AS (
  SELECT unnest(ARRAY[
    'BC PST',
    'B.C. PST Adjustment',
    'BUS. SERVICES GST',
    'CPS GST 100652692',
    'CPS GST ADJUSTMENT 362037',
    'CPS PST BRITISH COLUMBIA 7%',
    'FP GST Credit',
    'FP PST Credit',
    'GST',
    'GST adj',
    'GST ADJUSTMENT',
    'GST/HST',
    'GST/HST ADJUSTMENT',
    'GST Tax Adjustment',
    'PQ PST',
    'PST',
    'PST ADJUSTMENT',
    'PST-BC',
    'PST-BC adj',
    'PST-MB',
    'PST-QC'
  ]::text[]) AS detail_d
),
src AS (
  SELECT
    r.sheet_name,
    r.amount,
    date_trunc('month', r.statement_date)::date AS month_start,
    TRIM(r.detail_description) AS detail_d,
    TRIM(COALESCE(r.statement_category, '')) AS stmt_cat,
    TRIM(COALESCE(r.source_id::text, '')) AS sid_raw,
    EXISTS (SELECT 1 FROM hw_detail h WHERE h.detail_d = TRIM(r.detail_description)) AS is_hw,
    TRIM(LOWER(COALESCE(r.source, ''))) = 'wireless' AS is_wireless
  FROM raw_telus_spend AS r
  WHERE (TRIM(r.detail_description) NOT IN (SELECT ed.detail_d FROM excl_detail ed)
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