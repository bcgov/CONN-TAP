-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- Rows outside the Taxes statement_category whose detail_description looks tax-like
-- (gst/pst/hst/qst, case-insensitive) but is not on the known allowlist below.

CREATE OR REPLACE FUNCTION telus_raw_validate_unlisted_tax_like_detail_descriptions (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  detail_description text
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT
    t.sheet_name,
    t.statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.detail_description) AS detail_description
  FROM raw_data.raw_telus_spend AS t
  WHERE trim(both FROM COALESCE(t.statement_category, '')) <> 'Taxes'
    AND t.detail_description IS NOT NULL
    AND trim(both FROM t.detail_description) <> ''
    AND (
            trim(both FROM t.detail_description) ILIKE '%gst%'
         OR trim(both FROM t.detail_description) ILIKE '%pst%'
         OR trim(both FROM t.detail_description) ILIKE '%hst%'
         OR trim(both FROM t.detail_description) ILIKE '%qst%'
        )
    AND trim(both FROM t.detail_description) NOT IN (
      'B.C. PST Adjustment',
      'CPS GST 100652692',
      'CPS PST BRITISH COLUMBIA 7%',
      'FP GST Credit',
      'FP PST Credit',
      'GST adj',
      'GST Tax Adjustment',
      'IP TRUNKING PSTN CONNECTION*',
      'IP TRUNKING PSTN CONNECTION 3Y-BC*',
      'NGSTAT5IP STATIC IP 5IP',
      'PRI STARTER BUNDLE ADD''L PSTN LINK*',
      'PST-BC adj'
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name,
    statement_category,
    detail_description;
$$;
