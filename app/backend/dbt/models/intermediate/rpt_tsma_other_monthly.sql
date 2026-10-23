{{ config(materialized='view') }}

-- TSMA Time Limited Services spend (Managed Router, Managed Security, Managed WLAN) per
-- feed, customer, BGE and month, for the spend report. A pivot of rpt_spend_lines, which
-- holds the rules (section, BGE, ECC row, category). The raw customer name (rcid_cust_nm)
-- is display detail: the report's Time Limited Services section has a row per customer.
-- Filter on month_start when querying: each query recomputes from raw rows.

with customers as (
    select 'tsma_other_managed_router'::text as source_table, raw_id, rcid_cust_nm
    from {{ source('raw_data', 'tsma_other_managed_router') }}
    union all
    select 'tsma_other_managed_security', raw_id, rcid_cust_nm
    from {{ source('raw_data', 'tsma_other_managed_security') }}
    union all
    select 'tsma_wireline', raw_id, rcid_cust_nm
    from {{ source('raw_data', 'tsma_wireline') }}
)

select
    -- the report's feed name; 'managed wlan' is a wireline tower code
    case l.lookup_code when 'managed wlan' then 'managed_wlan_wifi' else l.lookup_code end as feed,
    nullif(trim(c.rcid_cust_nm), '') as rcid_cust_nm,
    l.entity_key,
    l.month_start,
    sum(l.spend_amount) as amount
from {{ ref('rpt_spend_lines') }} l
left join customers c on c.source_table = l.source_table and c.raw_id = l.raw_id
where l.section = 'tsma_time_limited'
group by 1, 2, 3, 4
