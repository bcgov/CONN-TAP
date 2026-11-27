-- The months each tracked vendor report has data for. Source for reporting_status,
-- which compares these months with the months the dashboard has selected.
--
-- Whether a report has arrived is not organization data, so there is no row-level
-- security: every role sees every row. Org roles still need the grant, since
-- analytics tables are closed to them by default.
{{ config(
    materialized='table',
    post_hook="grant select on {{ this }} to tap_org_admin, tap_org_user"
) }}

with report_months as (
    select distinct
        case source_table
            when 'raw_rogers_spend_cellular'   then 'Rogers Cellular'
            when 'raw_rogers_spend_data_voice' then 'Rogers Data'
            when 'raw_telus_spend'             then 'TELUS'
            when 'tsma_wireless'               then 'TSMA'
            when 'tsma_wireline'               then 'TSMA'
            when 'tsma_ivr'                    then 'TSMA'
            when 'tsma_mms'                    then 'TSMA'
            when 'tsma_lite_wireless'          then 'TSMA Lite'
            when 'tsma_lite_wireline'          then 'TSMA Lite'
        end as report_name,
        period_key
    from {{ ref('fct_service_spend') }}
)

select
    report_name,
    period_key
from report_months
-- TSMA Other is not tracked in the reporting status.
where report_name is not null
