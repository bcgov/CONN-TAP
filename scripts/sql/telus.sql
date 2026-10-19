-- TELUS NGTA spend report input: one row per tab and month, in the report's buckets.
-- All rules (exclusions, hardware, Wireless-first, unconfirmed source IDs -> Other,
-- PHSA Other -> Data) live in dbt: stg_telus_ngta_spend -> int_telus_ngta_spend ->
-- rpt_telus_ngta_monthly. This only reads that view, which reads raw data live, so a
-- newly ingested month is included without publishing anything.
-- Needs the dbt views to exist and be current: run
--   dbt run --select staging intermediate
-- after any dbt model or seed change. Save the result as scripts/source/telus_ngta_spend.csv.
SELECT
  'telus'::text AS provider,
  sheet_name    AS entity_key,
  month_start,
  cellular_hardware,
  cellular_plans,
  data_spend,
  voice_spend,
  other_spend,
  total_reported
FROM intermediate.rpt_telus_ngta_monthly
ORDER BY month_start, entity_key;
