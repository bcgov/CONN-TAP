{{ config(materialized='table', tags=['report']) }}

-- TELUS NGTA spend per tab and month, in the spend report's five buckets.
-- A table, so the spend report reads stored results. Tagged 'report': the deploy skips
-- it and the spend report runbook rebuilds it before each report.
-- All classification lives upstream; this only maps dbt categories to report buckets.

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
