-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15'). Alias matching goes through
-- telus_bge_alias_matches, so 00_bge_alias_matches.sql must be loaded first.

-- Sub-BGE counterpart of telus_raw_validate_new_bges_in_sheets, keyed on account_description
-- (Telus's sub-organization / billing account). Detects account_descriptions that are new
-- and/or unrecognized this month vs. the prior month. Returns one row per flagged value:
--   'Unmapped'            — absent last month AND not a recognized sub-BGE
--   'Persisting Unmapped' — present last month but not a recognized sub-BGE
--   'New Match'           — new this month but a recognized sub-BGE
--   'Disappeared'         — present last month, gone this month
-- "Recognized" means account_description matches a known alias in sub_bge_alias_map -- exact
-- normalized-key equality (norm_key), mirroring the pipeline (stg_telus_ngta_spend), NOT
-- substring. Recognition is by ALIAS MEMBERSHIP only: we do NOT require the alias to resolve to
-- a reference_data.sub_bge, because sub_bge_alias_map intentionally carries aliases for retired /
-- not-yet-loaded sub_bges and those are still "known". So only account_descriptions that match
-- NO alias are flagged new/unrecognized -- i.e. genuinely new spellings that need mapping.
-- p_statement_month is required.

DROP FUNCTION IF EXISTS telus_raw_validate_new_sub_bges_in_accounts (date);
CREATE OR REPLACE FUNCTION telus_raw_validate_new_sub_bges_in_accounts (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year  int,
  contradiction_month int,
  account_description text,
  status              text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  IF p_statement_month IS NULL THEN
    RAISE EXCEPTION 'telus_raw_validate_new_sub_bges_in_accounts: p_statement_month is required';
  END IF;

  RETURN QUERY
  WITH current_subs AS (
    SELECT DISTINCT trim(both FROM t.account_description) AS account_description
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
  ),
  prior_subs AS (
    SELECT DISTINCT trim(both FROM t.account_description) AS account_description
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month - interval '1 month')
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
  ),
  -- An account_description is "recognized" when its normalized key exactly matches ANY
  -- sub_bge_alias_map raw_name -- i.e. it is already a known alias. Recognition is by ALIAS
  -- MEMBERSHIP only: we do NOT additionally require the alias to resolve to a
  -- reference_data.sub_bge, because sub_bge_alias_map intentionally carries aliases for retired
  -- / not-yet-loaded sub_bges, and those are still "known" (already mapped) so flagging them
  -- would be noise. Only account_descriptions that match NO alias are new/unrecognized.
  -- norm_key: lower -> strip non-ASCII-printable -> collapse whitespace -> trim
  -- (kept in sync with the norm_key macro used in stg_telus_ngta_spend).
  recognized_subs AS (
    SELECT DISTINCT cs.account_description
    FROM current_subs AS cs
    JOIN seeds.sub_bge_alias_map AS sbm
      ON trim(regexp_replace(regexp_replace(lower(sbm.raw_name), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g'))
       = trim(regexp_replace(regexp_replace(lower(cs.account_description), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g'))
  )
  -- Current month: newly appeared and/or unrecognized account_descriptions
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int AS contradiction_year,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int AS contradiction_month,
    cs.account_description AS account_description,
    CASE
      WHEN NOT EXISTS (SELECT 1 FROM recognized_subs AS rs WHERE rs.account_description = cs.account_description)
       AND NOT EXISTS (SELECT 1 FROM prior_subs AS ps WHERE lower(ps.account_description) = lower(cs.account_description))
        THEN 'Unmapped'
      WHEN NOT EXISTS (SELECT 1 FROM recognized_subs AS rs WHERE rs.account_description = cs.account_description)
        THEN 'Persisting Unmapped'
      ELSE 'New Match'
    END AS status
  FROM current_subs AS cs
  WHERE NOT EXISTS (SELECT 1 FROM recognized_subs AS rs WHERE rs.account_description = cs.account_description)
     OR NOT EXISTS (SELECT 1 FROM prior_subs AS ps WHERE lower(ps.account_description) = lower(cs.account_description))

  UNION ALL

  -- Prior month: account_descriptions that have disappeared
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    ps.account_description,
    'Disappeared'::text
  FROM prior_subs AS ps
  WHERE NOT EXISTS (
    SELECT 1 FROM current_subs AS cs WHERE lower(cs.account_description) = lower(ps.account_description)
  )

  ORDER BY status, account_description;
END;
$$;
