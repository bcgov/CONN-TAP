-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15'). Alias matching goes through
-- telus_bge_alias_matches, so 00_bge_alias_matches.sql must be loaded first.

-- Detects sheet names that are new and/or unrecognized this month vs. the prior month.
-- Returns one row per flagged sheet with a status:
--   'Unmapped'            — absent last month AND not a recognized BGE
--   'Persisting Unmapped' — present last month but not a recognized BGE
--   'New Match'           — new this month but a recognized BGE
--   'Disappeared'         — present last month, gone this month
-- "Recognized" means the sheet matches an alias that resolves to a reference_data.bge code
-- (or the intentional ECC alias), the same source of truth as telus_raw_validate_all_bges_in_sheets.
-- Comparison is case-insensitive. p_statement_month is required — pass any date within the target month.

DROP FUNCTION IF EXISTS telus_raw_validate_new_bges_in_sheets (date);
CREATE OR REPLACE FUNCTION telus_raw_validate_new_bges_in_sheets (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year  int,
  contradiction_month int,
  sheet_name          text,
  status              text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  IF p_statement_month IS NULL THEN
    RAISE EXCEPTION 'telus_raw_validate_new_bges_in_sheets: p_statement_month is required';
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
  ),
  -- A sheet is "recognized" when it matches an alias that resolves to a real
  -- reference_data.bge code, or the intentional ECC alias
  recognized_sheets AS (
    SELECT DISTINCT cs.sheet_name
    FROM current_sheets AS cs
    JOIN seeds.bge_alias_map AS bam
      ON telus_bge_alias_matches(cs.sheet_name, bam.raw_name)
    WHERE bam.bge_alias = 'ECC'
       OR EXISTS (SELECT 1 FROM reference_data.bge AS b WHERE b.code = bam.bge_alias)
  )
  -- Current month: newly appeared and/or unrecognized sheets
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int AS contradiction_year,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int AS contradiction_month,
    cs.sheet_name AS sheet_name,
    CASE
      WHEN NOT EXISTS (SELECT 1 FROM recognized_sheets AS rs WHERE rs.sheet_name = cs.sheet_name)
       AND NOT EXISTS (SELECT 1 FROM prior_sheets AS ps WHERE lower(ps.sheet_name) = lower(cs.sheet_name))
        THEN 'Unmapped'
      WHEN NOT EXISTS (SELECT 1 FROM recognized_sheets AS rs WHERE rs.sheet_name = cs.sheet_name)
        THEN 'Persisting Unmapped'
      ELSE 'New Match'
    END AS status
  FROM current_sheets AS cs
  WHERE NOT EXISTS (SELECT 1 FROM recognized_sheets AS rs WHERE rs.sheet_name = cs.sheet_name)
     OR NOT EXISTS (SELECT 1 FROM prior_sheets AS ps WHERE lower(ps.sheet_name) = lower(cs.sheet_name))

  UNION ALL

  -- Prior month: sheets that have disappeared
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    ps.sheet_name,
    'Disappeared'::text
  FROM prior_sheets AS ps
  WHERE NOT EXISTS (
    SELECT 1 FROM current_sheets AS cs WHERE lower(cs.sheet_name) = lower(ps.sheet_name)
  )

  ORDER BY status, sheet_name;
END;
$$;
