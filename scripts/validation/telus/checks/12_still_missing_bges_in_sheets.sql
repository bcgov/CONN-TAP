-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15'). Alias matching goes through
-- telus_bge_alias_matches, so 00_bge_alias_matches.sql must be loaded first.

-- Month-over-month persistence of the "expected BGE not reporting" check
-- (telus_raw_validate_all_bges_in_sheets flags this for a single month). Returns every
-- reference_data.bge that has no matching sheet_name THIS month, annotated with whether it
-- was also absent LAST month:
--   'Still Missing' — absent this month AND last month (was flagged last month, still missing)
--   'Newly Missing' — absent this month but present last month (newly flagged)
-- A BGE is "present" in a month when some sheet_name matches one of its aliases, using the
-- same alias/SD-word-boundary matching and reference_data.bge join as all_bges_in_sheets.
-- p_statement_month is required — pass any date within the target month.

DROP FUNCTION IF EXISTS telus_raw_validate_still_missing_bges_in_sheets (date);
CREATE OR REPLACE FUNCTION telus_raw_validate_still_missing_bges_in_sheets (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year  int,
  contradiction_month int,
  bge_code            text,
  status              text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  IF p_statement_month IS NULL THEN
    RAISE EXCEPTION 'telus_raw_validate_still_missing_bges_in_sheets: p_statement_month is required';
  END IF;

  RETURN QUERY
  WITH current_sheets AS (
    SELECT DISTINCT trim(both FROM t.sheet_name) AS sheet_name
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      AND trim(both FROM t.sheet_name) IS NOT NULL
      AND trim(both FROM t.sheet_name) <> ''
  ),
  prior_sheets AS (
    SELECT DISTINCT trim(both FROM t.sheet_name) AS sheet_name
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month - interval '1 month')
      AND trim(both FROM t.sheet_name) IS NOT NULL
      AND trim(both FROM t.sheet_name) <> ''
  )
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int AS contradiction_year,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int AS contradiction_month,
    b.code AS bge_code,
    CASE
      WHEN NOT EXISTS (
             SELECT 1
             FROM prior_sheets AS sh
             JOIN seeds.bge_alias_map AS bam ON bam.bge_alias = b.code
             WHERE telus_bge_alias_matches(sh.sheet_name, bam.raw_name)
           )
        THEN 'Still Missing'
      ELSE 'Newly Missing'
    END AS status
  FROM reference_data.bge AS b
  -- Missing this month: no current sheet matches any alias of this BGE
  WHERE NOT EXISTS (
    SELECT 1
    FROM current_sheets AS sh
    JOIN seeds.bge_alias_map AS bam ON bam.bge_alias = b.code
    WHERE telus_bge_alias_matches(sh.sheet_name, bam.raw_name)
  )
  ORDER BY status, b.code;
END;
$$;
