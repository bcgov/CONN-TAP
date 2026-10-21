{{ config(materialized='view') }}

-- TSMA (main feeds only) spend per BGE and month, in the spend report's TSMA rows.
-- A view over int_service_spend_line_items, the same lines core.fct_service_spend is
-- built from, so the report uses dbt's BGE resolution as it is.
-- TSMA Lite and TSMA Other (Out of Scope) are still read by their own report SQL.
-- It reads raw data live, so a new month is visible straight after ingestion.
-- Filter on month_start when querying: each query recomputes from raw rows.

with tsma as (
    select
        li.period_key as month_start,
        li.source_table,
        b.code        as bge_code,
        sb.code       as sub_bge_code,
        cat.code      as category,
        li.spend_amount
    from {{ ref('int_service_spend_line_items') }} li
    left join {{ source('reference_data', 'bge') }} b on b.id = li.bge_id
    left join {{ source('reference_data', 'sub_bge') }} sb on sb.id = li.sub_bge_id
    left join {{ source('reference_data', 'service_category') }} cat on cat.id = li.service_category_id
    where li.source_table in ('tsma_wireless', 'tsma_wireline', 'tsma_mms', 'tsma_ivr')
)

select
    -- The workbook keeps ECC as its own row; dbt holds it as the 'Education and Child Care'
    -- sub-BGE under Gov BC. Open decision, as for TELUS and Rogers.
    case when sub_bge_code = 'Education and Child Care' then 'ECC' else bge_code end as entity_key,
    month_start,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_wireless'), 0) as cellular_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_mms'), 0)      as mms_spend,
    -- Wireline: only the towers dbt categorises as data or voice (Business Internet, Data - WAN /
    -- Conferencing, Long Distance, Voice). Other towers stay out of the report's rows (TSMA-4);
    -- Managed WLAN is reported under Out of Scope by tsma_other_spend.sql.
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_wireline' and category = 'data'), 0)  as data_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_wireline' and category = 'voice'), 0) as voice_spend,
    coalesce(sum(spend_amount) filter (where source_table = 'tsma_ivr'), 0)      as voice_ivr_spend
from tsma
group by 1, 2
