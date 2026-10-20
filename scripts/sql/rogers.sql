-- Rogers NGTA spend report input: one row per BGE and month, in the report's buckets.
-- All rules (hardware split, product-line categories, BGE and sub-BGE resolution,
-- school districts) live in dbt: stg_rogers_spend -> int_rogers_ngta_spend ->
-- int_service_spend_line_items -> rpt_rogers_ngta_monthly. This only reads that view,
-- which reads raw data live, so a newly ingested month is included without publishing anything.
-- Needs the dbt views to exist and be current: run
--   dbt run --select staging intermediate
-- after any dbt model or seed change. Save the result as scripts/source/rogers_ngta_spend.csv.
SELECT
  'rogers'::text AS provider,
  entity_key,
  month_start,
  cellular_hardware,
  cellular_plans,
  data_spend,
  voice_spend,
  other_spend,
  total_reported
FROM intermediate.rpt_rogers_ngta_monthly
ORDER BY month_start, entity_key;
