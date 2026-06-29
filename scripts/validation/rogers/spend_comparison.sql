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
-- =====================================================================
CREATE OR REPLACE FUNCTION raw_data.fn_rogers_spend_comparison(
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
WITH bge_map AS (
  SELECT *
  FROM (VALUES
    ('BC LOTTERY', 'BCLC'),
    ('BC LOTTERY CORPORATION', 'BCLC'),
    ('BRITISH COLUMBIA LOTTERY CORPORATION', 'BCLC'),
    ('BRITISH COLOMBIA LOTTERY CORPORATION', 'BCLC'),

    ('BC HYDRO', 'BC Hydro'),
    ('BRITISH COLUMBIA HYDRO', 'BC Hydro'),
    ('BRITISH COLUMBIA HYDRO & POWER AUTHORITY', 'BC Hydro'),

    ('EDUCATION AND CHILD CARE', 'ECC'),
    ('MINISTRY OF EDUCATION', 'ECC'),
    ('MINISTRY OF EDUCATION AND CHILD CARE', 'ECC'),
    ('BC MIN EDUCATION & CHILD CARE', 'ECC'),
    ('BC MIN EDUCATION AND CHILD CARE', 'ECC'),

    ('FRASER HEALTH AUTHORITY', 'FHA'),
    ('INTERIOR HEALTH AUTHORITY', 'IHA'),
    ('NORTHERN HEALTH AUTHORITY', 'NHA'),
    ('INSURANCE CORPORATION OF BRITISH COLUMB.', 'ICBC'),
    ('INSURANCE CORPORATION OF BRITISH COLUMBIA', 'ICBC'),
    ('PROVINCIAL HEALTH SERVICES AUTHORITY', 'PHSA'),
    ('VANCOUVER COASTAL HEALTH AUTHORITY', 'VCHA'),
    ('PROVIDENCE HEALTH CARE', 'VCHA'),
    ('VANCOUVER ISLAND HEALTH AUTHORITY', 'VIHA'),

    ('BC GOVERNMENT MINISTRIES', 'Gov BC'),
    ('BC MIN ATTORNEY GENERAL', 'Gov BC'),
    ('BC MIN CITIZENS'' SERVICES', 'Gov BC'),
    ('BC MIN HOUSING AND MUNICIPAL AFFAIRS', 'Gov BC'),
    ('BC MIN INDIGENOUS RELATIONS & RECONCIL.', 'Gov BC'),
    ('BC MIN JOBS AND ECONOMIC GROWTH', 'Gov BC'),
    ('BC MIN LABOUR', 'Gov BC'),
    ('BC MIN POST-SECONDARY ED & FUTURE SKILLS', 'Gov BC'),
    ('BC MIN SOCIAL DEV & POVERTY REDUCTION', 'Gov BC'),
    ('BC MIN TOURISM, ARTS, CULTURE, AND SPORT', 'Gov BC'),
    ('BC MIN TRANSPORTATION & TRANSIT', 'Gov BC'),
    ('INDIGENOUS RELATIONS AND RECONCILIATION', 'Gov BC'),
    ('JOB ECONOMIC DEVELOPMENT AND INNOVATION', 'Gov BC'),
    ('LAND AND WATER BC INC', 'Gov BC'),
    ('MIN OF FINANCE BC', 'Gov BC'),
    ('MIN OF JOBS TOURISM & INNOVATION', 'Gov BC'),
    ('MIN OF LABOUR', 'Gov BC'),
    ('MIN OF SOCIAL DEVELOPMENT', 'Gov BC'),
    ('MINISTRY OF CITIZENS SERVICES', 'Gov BC'),
    ('MINISTRY OF INFRASTRUCTURE', 'Gov BC'),
    ('OFFICE OF THE PREMIER', 'Gov BC'),
    ('TRANSPORTATION AND TRANSIT', 'Gov BC')
  ) AS m(alias, entity_key)
),
src AS (
  SELECT
    c.bge,
    c.sub_bge,
    (date_trunc('month', COALESCE(c.invoice_date, r.source_period)) - interval '1 month')::date AS month_start,
    COALESCE(c.hardware, 0)::numeric AS amount,
    'cellular_hardware'::text AS bucket
  FROM raw_data.raw_rogers_spend_cellular c
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = c.ingestion_run_id
  WHERE r.provider = 'rogers'

  UNION ALL

  SELECT
    c.bge,
    c.sub_bge,
    (date_trunc('month', COALESCE(c.invoice_date, r.source_period)) - interval '1 month')::date AS month_start,
    COALESCE(c.billed_amount_pre_tax, 0)::numeric
      - COALESCE(c.hardware, 0)::numeric AS amount,
    'cellular_plans'::text AS bucket
  FROM raw_data.raw_rogers_spend_cellular c
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = c.ingestion_run_id
  WHERE r.provider = 'rogers'

  UNION ALL

  SELECT
    v.bge,
    v.sub_bge,
    date_trunc('month', COALESCE(v.billingdate, r.source_period))::date AS month_start,
    COALESCE(v.billed_amount_pre_tax, 0)::numeric AS amount,
    CASE
      WHEN upper(trim(COALESCE(v.productline, ''))) = 'DATA' THEN 'data'
      WHEN upper(trim(COALESCE(v.productline, ''))) = 'VOICE' THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM raw_data.raw_rogers_spend_data_voice v
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = v.ingestion_run_id
  WHERE r.provider = 'rogers'
),
normalized AS (
  SELECT
    s.bge,
    s.sub_bge,
    s.month_start,
    s.amount,
    s.bucket,
    upper(trim(COALESCE(s.bge, ''))) AS bge_key,
    upper(trim(COALESCE(s.sub_bge, ''))) AS sub_bge_key
  FROM src s
),
bucketed AS (
  SELECT
    COALESCE(
      CASE
        WHEN sub_bge_key LIKE 'SCHOOL DISTRICT%'
          OR sub_bge_key LIKE 'DISTRICT%'
          OR bge_key LIKE 'SCHOOL DISTRICT%'
          OR bge_key LIKE 'DISTRICT%'
          THEN 'School Districts'
        WHEN sub_bge_key LIKE '%FAMILY MAINTENANCE AGENCY%'
          OR sub_bge_key LIKE '%PUBLIC SERVICE AGENCY%'
          THEN 'Gov BC'
        ELSE NULL
      END,
      sub_map.entity_key,
      bge_map.entity_key
    ) AS entity_key,
    month_start,
    amount,
    bucket
  FROM normalized n
  LEFT JOIN bge_map sub_map ON sub_map.alias = n.sub_bge_key
  LEFT JOIN bge_map bge_map ON bge_map.alias = n.bge_key
  WHERE month_start IS NOT NULL
),
-- One row per entity / month with a column per spend category.
monthly AS (
  SELECT
    entity_key,
    month_start,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_hardware'), 0) AS cellular_hardware,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_plans'), 0)    AS cellular_plans,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'data'), 0)             AS data_spend,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'voice'), 0)            AS voice_spend,
    COALESCE(SUM(amount) FILTER (WHERE bucket = 'other'), 0)           AS other_spend,
    COALESCE(SUM(amount), 0)                                            AS total_reported
  FROM bucketed
  WHERE entity_key IS NOT NULL
  GROUP BY entity_key, month_start
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
