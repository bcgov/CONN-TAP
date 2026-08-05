-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15'). Alias matching goes through
-- telus_bge_alias_matches, so 00_bge_alias_matches.sql must be loaded first.

-- Requires p_statement_month (one month only). Pass any date in that month (e.g. date '2026-03-15').
-- Fails when no sheet_name (for rows in that month) matches any alias for an expected BGE.
-- BGEs and aliases are sourced from reference_data.bge joined to seeds.bge_alias_map, so the
-- list stays in sync with reference data automatically. Alias matching goes through
-- telus_bge_alias_matches (whole-token match). NOTE: '…→ECC' aliases (MOE, etc.) do not join to
-- any BGE because ECC is not a reference_data.bge code, so a month whose only government sheet is
-- bare 'MOE' can flag Gov BC as missing.

CREATE OR REPLACE FUNCTION telus_raw_validate_all_bges_in_sheets (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year int,
  contradiction_month int,
  missing_bge text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  IF p_statement_month IS NULL THEN
    RAISE EXCEPTION 'telus_raw_validate_all_bges_in_sheets: p_statement_month is required';
  END IF;

  RETURN QUERY
  WITH base AS (
    SELECT DISTINCT trim(both FROM t.sheet_name) AS sheet_name
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      AND trim(both FROM t.sheet_name) IS NOT NULL
      AND trim(both FROM t.sheet_name) <> ''
  )
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int AS contradiction_year,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int AS contradiction_month,
    b.code AS missing_bge
  FROM reference_data.bge AS b
  WHERE NOT EXISTS (
    SELECT 1
    FROM base AS sh
    JOIN seeds.bge_alias_map AS bam ON bam.bge_alias = b.code
    WHERE telus_bge_alias_matches(sh.sheet_name, bam.raw_name)
  )
  ORDER BY b.code;
END;
$$;
