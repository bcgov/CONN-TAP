{{ config(materialized='view') }}

-- Rogers NGTA spend per BGE and month, in the spend report's five buckets.
-- A pivot of rpt_spend_lines, which holds the rules (section, BGE, ECC row, category).
-- Filter on month_start when querying: each query recomputes from raw rows.

select
    entity_key,
    month_start,
    coalesce(sum(spend_amount) filter (where category = 'cellular_hardware'), 0) as cellular_hardware,
    coalesce(sum(spend_amount) filter (where category = 'cellular'), 0)          as cellular_plans,
    coalesce(sum(spend_amount) filter (where category = 'data'), 0)              as data_spend,
    coalesce(sum(spend_amount) filter (where category = 'voice'), 0)             as voice_spend,
    -- Unknown (blank product line), or anything without a category, is the report's Unknown row
    coalesce(sum(spend_amount) filter (
        where category is null or category not in ('cellular_hardware', 'cellular', 'data', 'voice')
    ), 0)                                                                        as other_spend,
    coalesce(sum(spend_amount), 0)                                               as total_reported
from {{ ref('rpt_spend_lines') }}
where section = 'rogers_ngta'
group by entity_key, month_start
