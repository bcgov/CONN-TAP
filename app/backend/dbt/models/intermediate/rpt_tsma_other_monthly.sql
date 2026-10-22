{{ config(materialized='view') }}

-- TSMA Out of Scope spend (Managed Router, Managed Security, Managed WLAN) per customer and
-- month, for the spend report. A view over int_service_spend_line_items, the same lines
-- core.fct_service_spend is built from, so entity_key is dbt's BGE. The raw customer name
-- (rcid_cust_nm) is kept because the report's Out of Scope section has a row per customer.
-- It reads raw data live, so a new month is visible straight after ingestion.

with lines as (
    select
        li.source_table,
        li.raw_id,
        li.period_key as month_start,
        li.spend_amount,
        b.code  as bge_code,
        sb.code as sub_bge_code
    from {{ ref('int_service_spend_line_items') }} li
    left join {{ source('reference_data', 'bge') }} b on b.id = li.bge_id
    left join {{ source('reference_data', 'sub_bge') }} sb on sb.id = li.sub_bge_id
    where li.source_table in ('tsma_other_managed_router', 'tsma_other_managed_security', 'tsma_wireline')
),

customers as (
    select 'tsma_other_managed_router'::text as source_table, raw_id, 'managed_router'::text as feed, rcid_cust_nm
    from {{ source('raw_data', 'tsma_other_managed_router') }}
    union all
    select 'tsma_other_managed_security', raw_id, 'managed_security', rcid_cust_nm
    from {{ source('raw_data', 'tsma_other_managed_security') }}
    union all
    -- Managed WLAN is a tower in the main wireline feed
    select 'tsma_wireline', raw_id, 'managed_wlan_wifi', rcid_cust_nm
    from {{ source('raw_data', 'tsma_wireline') }}
    where lower(trim(tsma_service_tower)) = 'managed wlan'
)

select
    c.feed,
    nullif(trim(c.rcid_cust_nm), '') as rcid_cust_nm,
    -- The workbook keeps ECC as its own row; dbt holds it as the 'Education and Child Care'
    -- sub-BGE under Gov BC. Open decision, as for TELUS, Rogers and main TSMA.
    case when l.sub_bge_code = 'Education and Child Care' then 'ECC' else l.bge_code end as entity_key,
    l.month_start,
    sum(l.spend_amount) as amount
from lines l
inner join customers c on c.source_table = l.source_table and c.raw_id = l.raw_id
group by 1, 2, 3, 4
