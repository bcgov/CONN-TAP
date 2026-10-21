-- TSMA spend report inputs: run each query below and save it as the named CSV in scripts/source.
-- All rules (organisation fallback, BGE resolution, ECC row, which wireline towers count as
-- Data / Voice) live in dbt: stg_tsma_spend -> int_service_spend_line_items -> rpt_tsma_monthly.
-- These only read that view, which reads raw data live, so a newly ingested month is included
-- without publishing anything. entity_key is the dbt BGE code; tsma.py maps it to a workbook row.
-- Needs the dbt views to exist and be current: run
--   dbt run --select staging intermediate
-- after any dbt model or seed change.

===================tsma_cellular_spend=====================

SELECT entity_key, month_start, cellular_spend AS amount
FROM intermediate.rpt_tsma_monthly
WHERE month_start BETWEEN DATE '2024-01-01' AND DATE '2026-12-01'
  AND cellular_spend <> 0
ORDER BY entity_key, month_start;

===================tsma_data_spend=====================

SELECT entity_key, month_start, data_spend AS amount
FROM intermediate.rpt_tsma_monthly
WHERE month_start BETWEEN DATE '2024-01-01' AND DATE '2026-12-01'
  AND data_spend <> 0
ORDER BY entity_key, month_start;


====================tsma_voice_spend======================

SELECT entity_key, month_start, voice_spend AS amount
FROM intermediate.rpt_tsma_monthly
WHERE month_start BETWEEN DATE '2024-01-01' AND DATE '2026-12-01'
  AND voice_spend <> 0
ORDER BY entity_key, month_start;


==============tsma_mms_spend=========================

SELECT entity_key, month_start, mms_spend AS amount
FROM intermediate.rpt_tsma_monthly
WHERE month_start BETWEEN DATE '2024-01-01' AND DATE '2026-12-01'
  AND mms_spend <> 0
ORDER BY entity_key, month_start;


==================tsma_voice_ivr_spend=====================

SELECT entity_key, month_start, voice_ivr_spend AS amount
FROM intermediate.rpt_tsma_monthly
WHERE month_start BETWEEN DATE '2024-01-01' AND DATE '2026-12-01'
  AND voice_ivr_spend <> 0
ORDER BY entity_key, month_start;
