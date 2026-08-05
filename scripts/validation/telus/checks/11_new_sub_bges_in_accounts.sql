-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15').

-- Sub-BGE counterpart of telus_raw_validate_new_bges_in_sheets, keyed on account_description
-- (Telus's sub-organization / billing account).
--
-- Two independent questions, deliberately answered on two different bases:
--
--   RECOGNITION is about a raw SPELLING, so it compares raw text. The whole point is to catch
--   spellings the seeds do not have yet, and resolving first would silently discard exactly
--   those. A spelling is "recognized" when seeds.sub_bge_alias_map has a row for it -- alias
--   MEMBERSHIP only. We do NOT additionally require the alias to resolve to a
--   reference_data.sub_bge, because sub_bge_alias_map intentionally carries aliases for
--   retired / not-yet-loaded sub_bges (and aliases that route a sub-org back to its parent
--   BGE), and those are still "known".
--
--   APPEARANCE / DISAPPEARANCE is about an ENTITY, so it compares the resolved canonical code
--   (sub_bge_alias_map.sub_bge_alias). Providers re-spell the same organization constantly;
--   comparing raw text made every rename read as one organization leaving and another
--   arriving. Mirrors rogers_*_new_removed_detection.
--
-- Statuses (shared with telus_raw_validate_new_bges_in_sheets):
--   'Unmapped'            -- spelling in the current month, absent last month, no alias row
--   'Persisting Unmapped' -- spelling in both months, still no alias row
--   'New Match'           -- resolved entity in the current month, absent last month
--   'Disappeared'         -- resolved entity last month, absent this month
--
-- The `entity` column therefore carries a canonical sub_bge code for the last two statuses and
-- the raw account_description for the first two -- an unrecognized spelling has no canonical
-- code by definition. It replaces the old `account_description` column, which is no longer
-- accurate for every row.
--
-- Matching uses the norm_key shape from the dbt macro (lower -> strip non-ASCII-printable ->
-- collapse whitespace -> trim), kept in sync with stg_telus_ngta_spend. It is spelled out
-- inline rather than calling raw_data.norm_key(): the Telus runner does not load
-- rogers/helpers/_shared.sql, so that function is not guaranteed to exist here.
--
-- p_statement_month is required.

DROP FUNCTION IF EXISTS telus_raw_validate_new_sub_bges_in_accounts (date);
CREATE OR REPLACE FUNCTION telus_raw_validate_new_sub_bges_in_accounts (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year  int,
  contradiction_month int,
  entity              text,
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
  -- Recognition set: alias MEMBERSHIP, whatever the alias targets.
  WITH sub_bge_known AS (
    SELECT DISTINCT
      trim(regexp_replace(regexp_replace(lower(sbm.raw_name), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g')) AS raw_name
    FROM seeds.sub_bge_alias_map AS sbm
  ),
  -- Resolution set: only aliases that land on a real reference_data.sub_bge. 12 of the alias
  -- targets are BGE codes (e.g. 'VANCOUVER COASTAL HEALTH' -> 'VCHA (+PHC)'), used where the
  -- account_description names the parent organisation and there is no sub-org to point at.
  -- Those spellings are still RECOGNIZED above, but they are not sub-BGE entities, so they
  -- must not show on this tab as a SUB-BGE appearing or disappearing.
  sub_bge_resolve AS (
    SELECT DISTINCT
      trim(regexp_replace(regexp_replace(lower(sbm.raw_name), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g')) AS raw_name,
      sb.code AS code
    FROM seeds.sub_bge_alias_map AS sbm
    JOIN reference_data.sub_bge AS sb ON sb.code = sbm.sub_bge_alias
  ),
  -- Raw spellings per month (recognition side).
  current_raw AS (
    SELECT DISTINCT
      trim(regexp_replace(regexp_replace(lower(t.account_description), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g')) AS value
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
  ),
  prior_raw AS (
    SELECT DISTINCT
      trim(regexp_replace(regexp_replace(lower(t.account_description), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g')) AS value
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month - interval '1 month')
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
  ),
  -- Resolved entities per month (appearance / disappearance side). Spellings with no alias
  -- contribute nothing here -- they are reported as 'Unmapped' instead.
  current_res AS (
    SELECT DISTINCT r.code AS value
    FROM current_raw AS cr
    JOIN sub_bge_resolve AS r ON r.raw_name = cr.value
  ),
  prior_res AS (
    SELECT DISTINCT r.code AS value
    FROM prior_raw AS pr
    JOIN sub_bge_resolve AS r ON r.raw_name = pr.value
  )

  -- Unrecognized spellings in the current month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    cur.value,
    CASE WHEN EXISTS (SELECT 1 FROM prior_raw AS p WHERE p.value = cur.value)
         THEN 'Persisting Unmapped' ELSE 'Unmapped' END::text
  FROM current_raw AS cur
  WHERE NOT EXISTS (SELECT 1 FROM sub_bge_known AS k WHERE k.raw_name = cur.value)

  UNION ALL

  -- Entity in the current month but not the prior month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    cur.value,
    'New Match'::text
  FROM current_res AS cur
  WHERE NOT EXISTS (SELECT 1 FROM prior_res AS p WHERE p.value = cur.value)

  UNION ALL

  -- Entity in the prior month but not the current month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    pri.value,
    'Disappeared'::text
  FROM prior_res AS pri
  WHERE NOT EXISTS (SELECT 1 FROM current_res AS c WHERE c.value = pri.value)

  ORDER BY 4, 3;
END;
$$;
