{{ config(materialized='view') }}

-- Rogers NGTA spend per BGE and month, in the spend report's five buckets.
-- A view over int_service_spend_line_items, the same lines core.fct_service_spend is
-- built from, so the report uses dbt's BGE resolution and categories as they are.
-- It reads raw data live, so a new month is visible straight after ingestion,
-- before dbt publishes anything to core/analytics.
-- Filter on month_start when querying: each query recomputes from raw rows.

with rogers as (
    select
        li.period_key as month_start,
        b.code        as bge_code,
        sb.code       as sub_bge_code,
        cat.code      as category,
        li.spend_amount
    from {{ ref('int_service_spend_line_items') }} li
    left join {{ source('reference_data', 'bge') }} b on b.id = li.bge_id
    left join {{ source('reference_data', 'sub_bge') }} sb on sb.id = li.sub_bge_id
    left join {{ source('reference_data', 'service_category') }} cat on cat.id = li.service_category_id
    where li.source_table in ('raw_rogers_spend_cellular', 'raw_rogers_spend_data_voice')
)

select
    -- The workbook keeps ECC as its own row; dbt holds it as the 'Education and Child Care'
    -- sub-BGE under Gov BC. Open decision: ROG-6 in docs/rogers_ngta_deviations.md.
    case when sub_bge_code = 'Education and Child Care' then 'ECC' else bge_code end as entity_key,
    month_start,
    coalesce(sum(spend_amount) filter (where category = 'cellular_hardware'), 0) as cellular_hardware,
    coalesce(sum(spend_amount) filter (where category = 'cellular'), 0)          as cellular_plans,
    coalesce(sum(spend_amount) filter (where category = 'data'), 0)              as data_spend,
    coalesce(sum(spend_amount) filter (where category = 'voice'), 0)             as voice_spend,
    -- Unknown (blank product line), or anything without a category, is the report's Other
    coalesce(sum(spend_amount) filter (
        where category is null or category not in ('cellular_hardware', 'cellular', 'data', 'voice')
    ), 0)                                                                        as other_spend,
    coalesce(sum(spend_amount), 0)                                               as total_reported
from rogers
group by 1, 2
