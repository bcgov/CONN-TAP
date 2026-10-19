{{ config(materialized='view') }}

-- TELUS NGTA spend per tab and month, in the spend report's five buckets.
-- A view: it reads raw data live through int_telus_ngta_spend, so a new month is
-- visible straight after ingestion, before dbt publishes anything to core/analytics.
-- All classification lives upstream; this only maps dbt categories to report buckets.
-- Filter on month_start when querying: each query recomputes from raw rows.

with telus as (
    select sheet_name, organization_name, month_start, lookup_code, spend_amount
    from {{ ref('int_telus_ngta_spend') }}
),

telus_categories as (
    select sc.code, cat.code as category
    from {{ source('reference_data', 'service_code') }} sc
    join {{ source('reference_data', 'provider') }} p on p.id = sc.provider_id
    join {{ source('reference_data', 'service_category') }} cat on cat.id = sc.service_category_id
    where sc.source_system = 'ngta'
        and p.code = 'telus'
)

select
    t.sheet_name,
    t.organization_name,
    t.month_start,
    coalesce(sum(t.spend_amount) filter (where c.category = 'cellular_hardware'), 0) as cellular_hardware,
    coalesce(sum(t.spend_amount) filter (where c.category = 'cellular'), 0)          as cellular_plans,
    coalesce(sum(t.spend_amount) filter (where c.category = 'data'), 0)              as data_spend,
    coalesce(sum(t.spend_amount) filter (where c.category = 'voice'), 0)             as voice_spend,
    -- Unknown (telus_other), or anything without a category, is the report's Other
    coalesce(sum(t.spend_amount) filter (
        where c.category is null or c.category not in ('cellular_hardware', 'cellular', 'data', 'voice')
    ), 0)                                                                            as other_spend,
    coalesce(sum(t.spend_amount), 0)                                                 as total_reported
from telus t
left join telus_categories c on c.code = t.lookup_code
group by 1, 2, 3
