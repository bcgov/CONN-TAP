-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. p_statement_month is required -- pass any date within
-- the target month (e.g. date '2026-03-15').

-- Sub-BGE counterpart of telus_raw_validate_new_bges_in_sheets, keyed on account_description
-- (Telus's sub-organization / billing account).
--
-- Two independent questions, deliberately answered on two different bases:
--
--   RECOGNITION is about a raw SPELLING. A spelling is "recognized" when seeds.sub_bge_alias_map
--   has a row with the same reference_data.match_key -- alias MEMBERSHIP only. We do NOT
--   additionally require the alias to resolve to a reference_data.sub_bge, because
--   sub_bge_alias_map intentionally carries aliases for retired / not-yet-loaded sub_bges (and
--   aliases that route a sub-org back to its parent BGE), and those are still "known".
--
--   APPEARANCE / DISAPPEARANCE is about an ENTITY, so it compares the resolved canonical code
--   (sub_bge_alias_map.sub_bge_alias). Providers re-spell the same organization constantly;
--   comparing raw text made every rename read as one organization leaving and another
--   arriving. Mirrors rogers_*_new_removed_detection.
--
-- A sub-BGE is "new" when it is not in any previous month's report, or its spelling is not in
-- the seeded alias list. One that skipped a month and came back is not new, so it is not flagged.
--
-- Statuses (shared with telus_raw_validate_new_bges_in_sheets):
--   'Unmapped'            -- spelling in the current month, absent last month, no alias row
--   'Persisting Unmapped' -- spelling in both months, still no alias row
--   'New Match'           -- resolved entity in the current month, never seen in any earlier month
--   'Disappeared'         -- resolved entity last month, absent this month
--   'Still Disappeared'   -- resolved entity two months ago, absent last month and this month
--                            (i.e. 'Disappeared' in last month's report and still missing)
--
-- The `entity` column therefore carries a canonical sub_bge code for the last two statuses and
-- the raw account_description (norm_key-cleaned) for the first two -- an unrecognized spelling
-- has no canonical code by definition. It replaces the old `account_description` column, which
-- is no longer accurate for every row.
--
-- Matching uses reference_data.match_key -- the same key stg_telus_ngta_spend joins
-- sub_bge_alias_map on -- so this tab flags exactly the spellings dbt fails to resolve.
-- match_key drops punctuation and filler words and reduces school districts to their number,
-- so 'School District No 34 (Abbotsford)' and 'SCHOOL DISTRICT NO 34 ABBOTSFORD' are one
-- spelling here, as they are in dbt. "Spelling" below means a distinct match_key.
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
    SELECT DISTINCT reference_data.match_key(sbm.raw_name) AS mk
    FROM seeds.sub_bge_alias_map AS sbm
  ),
  -- Resolution set: only aliases that land on a real reference_data.sub_bge. 12 of the alias
  -- targets are BGE codes (e.g. 'VANCOUVER COASTAL HEALTH' -> 'VCHA (+PHC)'), used where the
  -- account_description names the parent organisation and there is no sub-org to point at.
  -- Those spellings are still RECOGNIZED above, but they are not sub-BGE entities, so they
  -- must not show on this tab as a SUB-BGE appearing or disappearing.
  sub_bge_resolve AS (
    SELECT DISTINCT
      reference_data.match_key(sbm.raw_name) AS mk,
      sb.code AS code
    FROM seeds.sub_bge_alias_map AS sbm
    JOIN reference_data.sub_bge AS sb ON sb.code = sbm.sub_bge_alias
  ),
  -- Spellings per month (recognition side): one row per match_key, displayed as the
  -- norm_key-cleaned raw text (min() picks one when several raw spellings share a key).
  current_raw AS (
    SELECT
      reference_data.match_key(t.account_description) AS mk,
      min(reference_data.norm_key(t.account_description)) AS value
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
    GROUP BY 1
  ),
  prior_raw AS (
    SELECT DISTINCT reference_data.match_key(t.account_description) AS mk
    FROM raw_data.raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month - interval '1 month')
      AND trim(both FROM t.account_description) IS NOT NULL
      AND trim(both FROM t.account_description) <> ''
  ),
  -- Every entity seen in any earlier month ("previous reports"). match_key runs once per
  -- distinct description, not once per raw row.
  history_res AS (
    SELECT DISTINCT r.code AS value
    FROM (
      SELECT DISTINCT t.account_description
      FROM raw_data.raw_telus_spend AS t
      WHERE t.statement_date IS NOT NULL
        AND t.statement_date < date_trunc('month', p_statement_month)
        AND trim(both FROM t.account_description) IS NOT NULL
        AND trim(both FROM t.account_description) <> ''
    ) AS d
    JOIN sub_bge_resolve AS r ON r.mk = reference_data.match_key(d.account_description)
  ),
  two_months_ago_res AS (
    SELECT DISTINCT r.code AS value
    FROM (
      SELECT DISTINCT t.account_description
      FROM raw_data.raw_telus_spend AS t
      WHERE t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month - interval '2 months')
        AND trim(both FROM t.account_description) IS NOT NULL
        AND trim(both FROM t.account_description) <> ''
    ) AS d
    JOIN sub_bge_resolve AS r ON r.mk = reference_data.match_key(d.account_description)
  ),
  -- Resolved entities per month (appearance / disappearance side). Spellings with no alias
  -- contribute nothing here -- they are reported as 'Unmapped' instead.
  current_res AS (
    SELECT DISTINCT r.code AS value
    FROM current_raw AS cr
    JOIN sub_bge_resolve AS r ON r.mk = cr.mk
  ),
  prior_res AS (
    SELECT DISTINCT r.code AS value
    FROM prior_raw AS pr
    JOIN sub_bge_resolve AS r ON r.mk = pr.mk
  )

  -- Unrecognized spellings in the current month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    cur.value,
    CASE WHEN EXISTS (SELECT 1 FROM prior_raw AS p WHERE p.mk = cur.mk)
         THEN 'Persisting Unmapped' ELSE 'Unmapped' END::text
  FROM current_raw AS cur
  WHERE NOT EXISTS (SELECT 1 FROM sub_bge_known AS k WHERE k.mk = cur.mk)

  UNION ALL

  -- Entity in the current month and in no earlier month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    cur.value,
    'New Match'::text
  FROM current_res AS cur
  WHERE NOT EXISTS (SELECT 1 FROM history_res AS h WHERE h.value = cur.value)

  UNION ALL

  -- Entity in the prior month but not the current month.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    pri.value,
    'Disappeared'::text
  FROM prior_res AS pri
  WHERE NOT EXISTS (SELECT 1 FROM current_res AS c WHERE c.value = pri.value)

  UNION ALL

  -- Entity flagged 'Disappeared' last month that is still gone.
  SELECT
    EXTRACT(YEAR  FROM date_trunc('month', p_statement_month))::int,
    EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
    tma.value,
    'Still Disappeared'::text
  FROM two_months_ago_res AS tma
  WHERE NOT EXISTS (SELECT 1 FROM prior_res AS p WHERE p.value = tma.value)
    AND NOT EXISTS (SELECT 1 FROM current_res AS c WHERE c.value = tma.value)

  ORDER BY 4, 3;
END;
$$;
