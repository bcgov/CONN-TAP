-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to that month.

-- Sheet mapping issues (the TELUS counterpart of the Rogers Mapping Issues check). A tab is a BGE; the accurate owner of a row is its account
-- (account_description -> sub_bge_alias_map -> sub_bge -> parent BGE), which is what dbt books.
-- Two conditions, one row per failing tab (or tab / account pair):
--
--   'Unmapped sheet'      -- the tab name has no alias in seeds.bge_alias_map, so dbt can't
--                            give it a BGE. Fix: add the tab name to bge_alias_map.csv.
--   'Account BGE differs' -- the account resolves to a sub_bge whose parent BGE isn't the tab's
--                            BGE, so dbt books the spend under a different BGE than the tab.
--                            Fix: correct the sub_bge_alias_map entry, or confirm the account
--                            really belongs to another BGE.
--
-- Matching is the dbt rule (reference_data.match_key equality, as in stg_telus_ngta_spend),
-- which is stricter than the whole-token containment used by the BGE checks 09-12. An ECC tab is
-- compared as Gov BC (ECC is a ministry under Gov BC, as in int_service_spend_line_items).
-- Accounts that don't resolve to a sub_bge are not flagged here (dbt uses the tab's BGE for
-- them); unrecognised accounts are reported by check 11.
--
-- Same rules as the dbt tests assert_telus_sheet_names_mapped_to_bge and
-- assert_telus_sheet_bge_matches_account_bge -- keep them in sync. Unlike those, this runs on
-- raw rows before the tax / payment exclusions, so amounts can differ slightly.

DROP FUNCTION IF EXISTS telus_raw_validate_sheet_mapping_issues (date);
CREATE OR REPLACE FUNCTION telus_raw_validate_sheet_mapping_issues (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  issue               text,
  sheet_name          text,
  tab_bge             text,
  account_description text,
  account_sub_bge     text,
  account_bge         text,
  first_month         date,
  last_month          date,
  row_count           bigint,
  amount              numeric
)
LANGUAGE sql
STABLE
AS $$
  -- One row per distinct tab / account, so match_key runs per name, not per raw row.
  WITH pairs AS (
    SELECT
      nullif(trim(regexp_replace(t.sheet_name, '[\x00-\x20\x7f]+', ' ', 'g')), '') AS sheet_name,
      nullif(trim(regexp_replace(t.account_description, '[\x00-\x20\x7f]+', ' ', 'g')), '') AS account_description,
      min(date_trunc('month', t.statement_date))::date AS first_month,
      max(date_trunc('month', t.statement_date))::date AS last_month,
      count(*) AS row_count,
      sum(t.amount) AS amount
    FROM raw_data.raw_telus_spend AS t
    WHERE p_statement_month IS NULL
       OR (
         t.statement_date IS NOT NULL
         AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
       )
    GROUP BY 1, 2
  ),
  bge_map AS (
    SELECT DISTINCT ON (reference_data.match_key(bam.raw_name))
      reference_data.match_key(bam.raw_name) AS mk,
      bam.bge_alias
    FROM seeds.bge_alias_map AS bam
    ORDER BY reference_data.match_key(bam.raw_name), bam.bge_alias
  ),
  sub_map AS (
    SELECT DISTINCT ON (reference_data.match_key(sbm.raw_name))
      reference_data.match_key(sbm.raw_name) AS mk,
      sbm.sub_bge_alias
    FROM seeds.sub_bge_alias_map AS sbm
    ORDER BY reference_data.match_key(sbm.raw_name), sbm.sub_bge_alias
  ),
  resolved AS (
    SELECT
      p.*,
      bm.bge_alias,
      tb.id   AS tab_bge_id,
      tb.code AS tab_bge,
      sb.code AS account_sub_bge,
      ab.id   AS account_bge_id,
      ab.code AS account_bge
    FROM pairs AS p
    LEFT JOIN bge_map AS bm
      ON bm.mk = reference_data.match_key(p.sheet_name)
    LEFT JOIN reference_data.bge AS tb
      ON reference_data.norm_key(tb.code) = reference_data.norm_key(
           CASE WHEN bm.bge_alias = 'ECC' THEN 'Gov BC' ELSE bm.bge_alias END)
    LEFT JOIN sub_map AS sm
      ON sm.mk = reference_data.match_key(p.account_description)
    LEFT JOIN reference_data.sub_bge AS sb
      ON reference_data.norm_key(sb.code) = reference_data.norm_key(sm.sub_bge_alias)
    LEFT JOIN reference_data.bge AS ab
      ON ab.id = sb.bge_id
  ),
  flagged AS (
    SELECT
      CASE WHEN r.bge_alias IS NULL THEN 'Unmapped sheet' ELSE 'Account BGE differs' END AS issue,
      r.sheet_name,
      r.tab_bge,
      -- An unmapped tab is reported once, not once per account.
      CASE WHEN r.bge_alias IS NULL THEN NULL ELSE r.account_description END AS account_description,
      CASE WHEN r.bge_alias IS NULL THEN NULL ELSE r.account_sub_bge END     AS account_sub_bge,
      CASE WHEN r.bge_alias IS NULL THEN NULL ELSE r.account_bge END         AS account_bge,
      r.first_month,
      r.last_month,
      r.row_count,
      r.amount
    FROM resolved AS r
    WHERE r.bge_alias IS NULL
       OR (r.account_bge_id IS NOT NULL AND r.account_bge_id IS DISTINCT FROM r.tab_bge_id)
  )
  SELECT
    f.issue,
    f.sheet_name,
    f.tab_bge,
    f.account_description,
    f.account_sub_bge,
    f.account_bge,
    min(f.first_month),
    max(f.last_month),
    sum(f.row_count)::bigint,
    sum(f.amount)
  FROM flagged AS f
  GROUP BY 1, 2, 3, 4, 5, 6
  ORDER BY 1 DESC, 2, 4;
$$;
