{{ config(materialized='view') }}

-- TELUS NGTA spend per tab and month, in the spend report's five buckets.
-- A view: it reads raw data live through int_telus_ngta_spend, so a new month is
-- visible straight after ingestion, before dbt publishes anything to core/analytics.
-- All classification lives upstream; this only maps dbt categories to report buckets.
-- Filter on month_start when querying: each query recomputes from raw rows.
-- lookup_code is the category code from the pricebook match.

with telus as (
    select sheet_name, organization_name, month_start, lookup_code, spend_amount
    from {{ ref('int_telus_ngta_spend') }}
)

select
    t.sheet_name,
    t.organization_name,
    t.month_start,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'cellular_hardware'), 0) as cellular_hardware,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'cellular'), 0)          as cellular_plans,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'data'), 0)              as data_spend,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'voice'), 0)             as voice_spend,
    -- Unknown, or any other category (Time Limited Services, Professional Services), is the report's Other
    coalesce(sum(t.spend_amount) filter (
        where t.lookup_code not in ('cellular_hardware', 'cellular', 'data', 'voice')
    ), 0)                                                                               as other_spend,
    coalesce(sum(t.spend_amount), 0)                                                    as total_reported
from telus t
group by 1, 2, 3
