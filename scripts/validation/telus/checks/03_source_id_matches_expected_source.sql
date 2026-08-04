-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- Expected: source_id 164 or 130 → source 'Wireless'; source_id 1001, 103, 104, 102, or 106
-- → source 'Wireline'. Any other source_id or any source other than those two is flagged.

CREATE OR REPLACE FUNCTION telus_raw_validate_source_id_matches_expected_source (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  source_id text,
  source text
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT
    t.sheet_name,
    t.statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.source_id) AS source_id,
    trim(both FROM t.source) AS source
  FROM raw_data.raw_telus_spend AS t
  WHERE NOT (
      (
        trim(both FROM COALESCE(t.source, '')) = 'Wireless'
        AND trim(both FROM COALESCE(t.source_id, '')) IN ('164', '130')
      )
      OR (
        trim(both FROM COALESCE(t.source, '')) = 'Wireline'
        AND trim(both FROM COALESCE(t.source_id, '')) IN ('1001', '103', '104', '102', '106')
      )
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
    source_id,
    source;
$$;
