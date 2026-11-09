{{ config(materialized='table', tags=['report']) }}

-- TELUS NGTA spend per tab and month, one column per spend report row.
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
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'time_limited_services'), 0) as tls_spend,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'professional_services'), 0) as professional_services_spend,
    coalesce(sum(t.spend_amount) filter (where t.lookup_code = 'ancillary_hardware'), 0)    as ancillary_hardware_spend,
    -- Unknown, or any other category, is the report's Unknown row
    coalesce(sum(t.spend_amount) filter (
        where t.lookup_code not in (
            'cellular_hardware', 'cellular', 'data', 'voice',
            'time_limited_services', 'professional_services', 'ancillary_hardware'
        )
    ), 0)                                                                               as other_spend,
    coalesce(sum(t.spend_amount), 0)                                                    as total_reported
from telus t
group by 1, 2, 3
