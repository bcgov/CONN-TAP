-- =====================================================================
-- Rogers month-over-month spend comparison
-- ---------------------------------------------------------------------
-- Call it with a year and a month, e.g.
--     SELECT * FROM raw_data.fn_rogers_spend_comparison(2025, 6);
--
-- For every entity (BGE) it returns, per spend category:
--   * <category>_current               -> spend in the requested month
--   * <category>_previous              -> spend in the month before
--   * <category>_difference            -> current - previous
--   * <category>_diff_over_50_percent  -> 'y' when the absolute difference
--                                         is greater than 50% of the
--                                         current month's value, else 'n'
--
-- Categories: cellular_hardware, cellular_plans, data, voice, other, total
--
-- p_source scopes which raw feed(s) are included:
--   NULL / 'all'  -> cellular + voice/data (default)
--   'cellular'    -> cellular feed only (data/voice/other categories come back 0)
--   'data_voice'  -> voice/data feed only (cellular categories come back 0)
-- =====================================================================
-- Needs the dbt views to exist and be current (dbt run --select staging intermediate).
DROP FUNCTION IF EXISTS raw_data.fn_rogers_spend_comparison(integer, integer);

CREATE OR REPLACE FUNCTION raw_data.fn_rogers_spend_comparison(
  p_year   integer,
  p_month  integer,
  p_source text DEFAULT NULL
)
RETURNS TABLE (
  provider                              text,
  entity_key                            text,
  report_month                          date,
  previous_month                        date,

  cellular_hardware_current             numeric,
  cellular_hardware_previous            numeric,
  cellular_hardware_difference          numeric,
  cellular_hardware_diff_over_50_percent text,

  cellular_plans_current                numeric,
  cellular_plans_previous               numeric,
  cellular_plans_difference             numeric,
  cellular_plans_diff_over_50_percent   text,

  data_current                          numeric,
  data_previous                         numeric,
  data_difference                       numeric,
  data_diff_over_50_percent             text,

  voice_current                         numeric,
  voice_previous                        numeric,
  voice_difference                      numeric,
  voice_diff_over_50_percent            text,

  other_current                         numeric,
  other_previous                        numeric,
  other_difference                      numeric,
  other_diff_over_50_percent            text,

  total_current                         numeric,
  total_previous                        numeric,
  total_difference                      numeric,
  total_diff_over_50_percent            text
)
LANGUAGE sql
STABLE
AS $$
-- Monthly totals come from intermediate.rpt_rogers_ngta_monthly, the dbt view the spend
-- report reads (scripts/rogers_ngta.py), so this check, the workbook and the dashboards
-- share one set of rules (hardware split, product-line categories, BGE resolution, ECC row).
-- Each feed fills its own columns: cellular -> hardware/plans, voice/data -> data/voice/other,
-- so p_source keeps only that feed's columns. Entities with nothing in scope are left out.
WITH scoped AS (
  SELECT
    -- ECC is its own row here, as in the workbook (the dashboards keep it under Gov BC).
    -- To match the dashboards instead: CASE WHEN v.entity_key = 'ECC' THEN 'Gov BC' ELSE v.entity_key END
    v.entity_key,
    v.month_start,
    CASE WHEN p_source = 'data_voice' THEN 0 ELSE v.cellular_hardware END AS cellular_hardware,
    CASE WHEN p_source = 'data_voice' THEN 0 ELSE v.cellular_plans    END AS cellular_plans,
    CASE WHEN p_source = 'cellular'   THEN 0 ELSE v.data_spend        END AS data_spend,
    CASE WHEN p_source = 'cellular'   THEN 0 ELSE v.voice_spend       END AS voice_spend,
    CASE WHEN p_source = 'cellular'   THEN 0 ELSE v.other_spend       END AS other_spend
  FROM intermediate.rpt_rogers_ngta_monthly v
  WHERE v.month_start IN (make_date(p_year, p_month, 1),
                          (make_date(p_year, p_month, 1) - interval '1 month')::date)
),
-- One row per entity / month with a column per spend category.
monthly AS (
  SELECT
    s.*,
    s.cellular_hardware + s.cellular_plans + s.data_spend + s.voice_spend + s.other_spend AS total_reported
  FROM scoped s
  WHERE (s.cellular_hardware, s.cellular_plans, s.data_spend, s.voice_spend, s.other_spend)
        <> (0, 0, 0, 0, 0)
),
-- The requested month and the month immediately before it.
target AS (
  SELECT
    make_date(p_year, p_month, 1)                              AS cur_month,
    (make_date(p_year, p_month, 1) - interval '1 month')::date AS prev_month
),
cur AS (
  SELECT m.* FROM monthly m, target t WHERE m.month_start = t.cur_month
),
prev AS (
  SELECT m.* FROM monthly m, target t WHERE m.month_start = t.prev_month
),
-- Pair each entity's current and previous month side by side.
joined AS (
  SELECT
    COALESCE(c.entity_key, p.entity_key)         AS entity_key,
    t.cur_month                                  AS report_month,
    t.prev_month                                 AS previous_month,

    COALESCE(c.cellular_hardware, 0) AS ch_cur, COALESCE(p.cellular_hardware, 0) AS ch_prev,
    COALESCE(c.cellular_plans, 0)    AS cp_cur, COALESCE(p.cellular_plans, 0)    AS cp_prev,
    COALESCE(c.data_spend, 0)        AS dt_cur, COALESCE(p.data_spend, 0)        AS dt_prev,
    COALESCE(c.voice_spend, 0)       AS vc_cur, COALESCE(p.voice_spend, 0)       AS vc_prev,
    COALESCE(c.other_spend, 0)       AS ot_cur, COALESCE(p.other_spend, 0)       AS ot_prev,
    COALESCE(c.total_reported, 0)    AS tt_cur, COALESCE(p.total_reported, 0)    AS tt_prev
  FROM cur c
  FULL OUTER JOIN prev p ON c.entity_key = p.entity_key
  CROSS JOIN target t
)
SELECT
  'rogers'::text AS provider,
  entity_key,
  report_month,
  previous_month,

  ch_cur, ch_prev, (ch_cur - ch_prev) AS cellular_hardware_difference,
  CASE WHEN ABS(ch_cur - ch_prev) > 0.5 * ABS(ch_cur) THEN 'y' ELSE 'n' END,

  cp_cur, cp_prev, (cp_cur - cp_prev) AS cellular_plans_difference,
  CASE WHEN ABS(cp_cur - cp_prev) > 0.5 * ABS(cp_cur) THEN 'y' ELSE 'n' END,

  dt_cur, dt_prev, (dt_cur - dt_prev) AS data_difference,
  CASE WHEN ABS(dt_cur - dt_prev) > 0.5 * ABS(dt_cur) THEN 'y' ELSE 'n' END,

  vc_cur, vc_prev, (vc_cur - vc_prev) AS voice_difference,
  CASE WHEN ABS(vc_cur - vc_prev) > 0.5 * ABS(vc_cur) THEN 'y' ELSE 'n' END,

  ot_cur, ot_prev, (ot_cur - ot_prev) AS other_difference,
  CASE WHEN ABS(ot_cur - ot_prev) > 0.5 * ABS(ot_cur) THEN 'y' ELSE 'n' END,

  tt_cur, tt_prev, (tt_cur - tt_prev) AS total_difference,
  CASE WHEN ABS(tt_cur - tt_prev) > 0.5 * ABS(tt_cur) THEN 'y' ELSE 'n' END
FROM joined
ORDER BY entity_key;
$$;
