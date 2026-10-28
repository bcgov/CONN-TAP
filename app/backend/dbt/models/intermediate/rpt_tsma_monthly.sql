{{ config(materialized='view') }}

-- TSMA (main feeds) spend per BGE and month, in the spend report's TSMA rows.
-- A pivot of rpt_spend_lines, which holds the rules (section, BGE, ECC row, category).
-- MMS and IVR are display splits of their category (by service code).
-- Time Limited Services lines are their own section (rpt_tsma_other_monthly).
-- Filter on month_start when querying: each query recomputes from raw rows.

select
    entity_key,
    month_start,
    coalesce(sum(spend_amount) filter (where category = 'cellular' and lookup_code <> 'mms'), 0) as cellular_spend,
    coalesce(sum(spend_amount) filter (where category = 'cellular' and lookup_code =  'mms'), 0) as mms_spend,
    coalesce(sum(spend_amount) filter (where category = 'data'), 0)                              as data_spend,
    coalesce(sum(spend_amount) filter (where category = 'voice'    and lookup_code <> 'ivr'), 0) as voice_spend,
    coalesce(sum(spend_amount) filter (where category = 'voice'    and lookup_code =  'ivr'), 0) as voice_ivr_spend,
    -- No workbook row for anything else (TSMA-4): reported here so tsma.py can warn about it
    coalesce(sum(spend_amount) filter (
        where category is null or category not in ('cellular', 'data', 'voice')
    ), 0)                                                                                        as other_spend
from {{ ref('rpt_spend_lines') }}
where section = 'tsma'
group by entity_key, month_start
