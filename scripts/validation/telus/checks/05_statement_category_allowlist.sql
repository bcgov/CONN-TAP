-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- statement_category must be one of the known Telus categories below (after trim). Any other
-- value, NULL, or all-whitespace is flagged. Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_statement_category_allowlist (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  contradiction_row_count bigint
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    t.sheet_name,
    trim(both FROM t.statement_category) AS statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    COUNT(*)::bigint AS contradiction_row_count
  FROM raw_data.raw_telus_spend AS t
  WHERE (
      t.statement_category IS NULL
      OR trim(both FROM t.statement_category) = ''
      OR trim(both FROM t.statement_category) NOT IN (
        'Adjustment',
        'Adjustments',
        'Alternate Services',
        'Amount due from last bill',
        'Amount Due from last bill',
        'Directory Advertising',
        'Other Charges and Credits',
        'Payment',
        'Payments',
        'Recurring Service Charges',
        'Taxes',
        'Usage'
      )
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
    trim(both FROM t.statement_category),
    EXTRACT(YEAR FROM t.statement_date)::int,
    EXTRACT(MONTH FROM t.statement_date)::int
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name NULLS LAST,
    statement_category NULLS LAST;
$$;
