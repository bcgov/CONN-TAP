-- =====================================================================
-- Telus month-over-month spend comparison
-- ---------------------------------------------------------------------
-- Call it with a year and a month, e.g.
--     SELECT * FROM raw_data.fn_telus_spend_comparison(2025, 6);
--
-- For every entity (sheet) it returns, per spend category:
--   * <category>_current               -> spend in the requested month
--   * <category>_previous              -> spend in the month before
--   * <category>_difference            -> current - previous
--   * <category>_diff_over_50_percent  -> 'y' when the absolute difference
--                                         is greater than 50% of the
--                                         current month's value, else 'n'
--
-- Categories: cellular_hardware, cellular_plans, data, voice, other, total
-- =====================================================================
CREATE OR REPLACE FUNCTION raw_data.fn_telus_spend_comparison(
  p_year  integer,
  p_month integer
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
WITH hw_detail AS (
  SELECT unnest(ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay. canc.',
    'device discount repay. - cr',
    'monthly easy payment',
    'telus easy payment balance',
    'equipment adjustment'
  ]::text[]) AS detail_d
),
excl_category AS (
  SELECT unnest(ARRAY[
    'payment',
    'payments',
    'amount due from last bill',
    'taxes'
  ]::text[]) AS stmt_cat
),
excl_detail AS (
  SELECT unnest(ARRAY[
    'bc pst',
    'b.c. pst adjustment',
    'bus. services gst',
    'cps gst 100652692',
    'cps gst adjustment 362037',
    'cps pst british columbia 7%',
    'fp gst credit',
    'fp pst credit',
    'gst',
    'gst adj',
    'gst adjustment',
    'gst/hst',
    'gst/hst adjustment',
    'gst tax adjustment',
    'pq pst',
    'pst',
    'pst adjustment',
    'pst-bc',
    'pst-bc adj',
    'pst-mb',
    'pst-qc'
  ]::text[]) AS detail_d
),
src AS (
  SELECT
    r.sheet_name,
    r.amount,
    date_trunc('month', r.statement_date)::date AS month_start,
    LOWER(TRIM(r.detail_description)) AS detail_d,
    LOWER(TRIM(COALESCE(r.statement_category, ''))) AS stmt_cat,
    TRIM(COALESCE(r.source_id::text, '')) AS sid_raw,
    EXISTS (SELECT 1 FROM hw_detail h WHERE h.detail_d = LOWER(TRIM(r.detail_description))) AS is_hw,
    TRIM(LOWER(COALESCE(r.source, ''))) = 'wireless' AS is_wireless
  FROM raw_data.raw_telus_spend AS r
  WHERE (LOWER(TRIM(r.detail_description)) NOT IN (SELECT ed.detail_d FROM excl_detail ed)
     OR r.detail_description IS NULL)
    AND COALESCE(LOWER(TRIM(r.statement_section)), '') <> 'balance forward'
),
flagged AS (
  SELECT
    sheet_name,
    month_start,
    amount,
    is_hw,
    is_wireless,
    CASE
      WHEN is_hw
        OR stmt_cat NOT IN (SELECT x.stmt_cat FROM excl_category x)
      THEN TRUE
      ELSE FALSE
    END AS is_included,
    CASE
      WHEN sid_raw ~ '^-?[0-9]+(\.[0-9]+)?$'
        THEN (sid_raw::numeric)::bigint::text
      WHEN sid_raw = '' THEN NULL
      ELSE sid_raw
    END AS sid_n
  FROM src
),
bucketed AS (
  SELECT
    sheet_name,
    month_start,
    amount,
    CASE
      WHEN is_hw THEN 'cellular_hardware'
      WHEN sid_n IN ('164','130') OR is_wireless THEN 'cellular_plans'
      WHEN sid_n IN ('1001', '103') THEN 'data'
      WHEN sid_n IN ('104', '102', '106') THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM flagged
  WHERE is_included
    AND month_start IS NOT NULL
    AND (NOT is_hw OR is_wireless)
),
-- One row per entity / month with a column per spend category.
monthly AS (
  SELECT
    sheet_name AS entity_key,
    month_start,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_hardware'), 0) AS cellular_hardware,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_plans'), 0)    AS cellular_plans,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'data'), 0)             AS data_spend,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'voice'), 0)            AS voice_spend,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'other'), 0)           AS other_spend,
    COALESCE(SUM(amount), 0)                                            AS total_reported
  FROM bucketed
  GROUP BY sheet_name, month_start
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
  'telus'::text AS provider,
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
