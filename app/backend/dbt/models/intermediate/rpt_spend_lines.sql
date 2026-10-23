{{ config(materialized='view') }}

-- One row per spend line, with the spend report's shared rules written once:
--   section     which workbook section the line belongs to
--   entity_key  the BGE the report shows it under (dbt's BGE, with the ECC row)
--   category    the service tower (dbt's category, from reference_data.service_code)
--   lookup_code the service code, for display splits within a category (MMS, IVR, ...)
-- The rpt_* views only pivot this into the workbook's columns.
-- A view over int_service_spend_line_items, the same lines core.fct_service_spend is
-- built from; it reads raw data live, so a new month is visible straight after ingestion.

select
    case
        when li.source_table = 'raw_telus_spend'
            then 'telus_ngta'
        when li.source_table in ('raw_rogers_spend_cellular', 'raw_rogers_spend_data_voice')
            then 'rogers_ngta'
        -- Managed Router / Security / WLAN, whichever TSMA feed they come from
        when cat.code = 'time_limited_services'
            then 'tsma_time_limited'
        when li.source_table in ('tsma_lite_wireless', 'tsma_lite_wireline')
            then 'tsma_lite'
        when li.source_table in ('tsma_wireless', 'tsma_wireline', 'tsma_mms', 'tsma_ivr')
            then 'tsma'
    end as section,
    -- The workbook keeps ECC as its own row; dbt holds it as the 'Education and Child Care'
    -- sub-BGE under Gov BC. Open decision (ECC).
    case when sb.code = 'Education and Child Care' then 'ECC' else b.code end as entity_key,
    li.period_key as month_start,
    cat.code      as category,
    li.lookup_code,
    li.source_table,
    li.raw_id,
    li.spend_amount
from {{ ref('int_service_spend_line_items') }} li
left join {{ source('reference_data', 'bge') }} b on b.id = li.bge_id
left join {{ source('reference_data', 'sub_bge') }} sb on sb.id = li.sub_bge_id
left join {{ source('reference_data', 'service_category') }} cat on cat.id = li.service_category_id
