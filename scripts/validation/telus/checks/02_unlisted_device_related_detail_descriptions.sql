-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- detail_description values that look device/hardware/equipment/Easy Payment related must match
-- a known allowlist (after trim). Heuristic: hardware, equipment (incl. typo equipement), easy pay /
-- easypay, or device (case-insensitive). Only rows whose source is NULL/blank or Wireless.
-- Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_unlisted_device_related_detail_descriptions (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  source text,
  contradiction_year int,
  contradiction_month int,
  detail_description text,
  contradiction_row_count bigint,
  contradiction_amount_sum numeric
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    t.sheet_name,
    t.statement_category,
    NULLIF(trim(both FROM t.source), '') AS source,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.detail_description) AS detail_description,
    COUNT(*)::bigint AS contradiction_row_count,
    SUM(t.amount) AS contradiction_amount_sum
  FROM raw_data.raw_telus_spend AS t
  WHERE (
      t.source IS NULL
      OR trim(both FROM t.source) = ''
      OR trim(both FROM t.source) = 'Wireless'
    )
    AND t.detail_description IS NOT NULL
    AND trim(both FROM t.detail_description) <> ''
    AND (
            trim(both FROM t.detail_description) ILIKE '%hardware%'
         OR trim(both FROM t.detail_description) ILIKE '%equipment%'
         OR trim(both FROM t.detail_description) ILIKE '%equipement%'
         OR trim(both FROM t.detail_description) ILIKE '%easypay%'
         OR trim(both FROM t.detail_description) ILIKE '%easy%pay%'
         OR trim(both FROM t.detail_description) ILIKE '%device%'
        )
    AND trim(both FROM t.detail_description) NOT IN (
      'Hardware Purchase Charge',
      'Device Discount Repayment',
      'Monthly TELUS Easy Payment',
      'Device discount repay. canc.',
      'Device discount repay. - CR',
      'Monthly Easy Payment',
      'TELUS Easy Payment Balance',
      'Equipment Adjustment'
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  GROUP BY
    t.sheet_name,
    t.statement_category,
    NULLIF(trim(both FROM t.source), ''),
    EXTRACT(YEAR FROM t.statement_date)::int,
    EXTRACT(MONTH FROM t.statement_date)::int,
    trim(both FROM t.detail_description)
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name NULLS LAST,
    statement_category NULLS LAST,
    source NULLS FIRST,
    detail_description;
$$;
