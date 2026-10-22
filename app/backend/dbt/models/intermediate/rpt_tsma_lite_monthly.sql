{{ config(materialized='view') }}

-- TSMA Lite spend per month, in the spend report's Lite section columns.
-- Reads stg_tsma_spend (the Lite branches), the same lines core.fct_service_spend is built
-- from. It uses staging rather than int_service_spend_line_items because the report splits
-- voice by tower (Conferencing / Long Distance / Voice), which line items only keep as a category.
-- All Lite spend is reported under School Districts (tsma.py), as every Lite customer
-- resolves to a school district today (LITE-2 in docs/tsma_deviations.md).
-- It reads raw data live, so a new month is visible straight after ingestion.

select
    month_start,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_lite_wireline' and tsma_service_tower = 'conferencing'), 0)  as conferencing_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_lite_wireline' and tsma_service_tower = 'long distance'), 0) as long_distance_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_lite_wireline' and tsma_service_tower = 'voice'), 0)         as voice_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_lite_wireless'), 0)                                         as cellular_spend
from {{ ref('stg_tsma_spend') }}
-- Other Lite wireline towers stay out of the report, as before (LITE-1: none today).
where source_table in ('tsma_lite_wireline', 'tsma_lite_wireless')
    and month_start is not null
group by month_start
