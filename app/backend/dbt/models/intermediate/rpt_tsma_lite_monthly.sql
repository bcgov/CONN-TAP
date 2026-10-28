{{ config(materialized='view') }}

-- TSMA Lite spend per month, in the spend report's Lite section columns.
-- A pivot of rpt_spend_lines, which holds the rules (section, category).
-- Conferencing and Long Distance are display splits of Voice (by service code).
-- All Lite spend is reported under School Districts (tsma.py), as every Lite customer
-- resolves to a school district today (LITE-2).
-- Filter on month_start when querying: each query recomputes from raw rows.

select
    month_start,
    coalesce(sum(spend_amount) filter (where category = 'voice' and lookup_code = 'conferencing'), 0)  as conferencing_spend,
    coalesce(sum(spend_amount) filter (where category = 'voice' and lookup_code = 'long distance'), 0) as long_distance_spend,
    coalesce(sum(spend_amount) filter (
        where category = 'voice' and lookup_code not in ('conferencing', 'long distance')
    ), 0)                                                                                             as voice_spend,
    coalesce(sum(spend_amount) filter (where category = 'cellular'), 0)                               as cellular_spend,
    -- No Lite row for anything else (LITE-1, e.g. a Data tower): reported here so tsma.py can warn
    coalesce(sum(spend_amount) filter (
        where category is null or category not in ('voice', 'cellular')
    ), 0)                                                                                             as other_spend
from {{ ref('rpt_spend_lines') }}
where section = 'tsma_lite'
group by month_start
