{{ config(materialized='materialized_view') }}

select
    dp.calendar_year,
    dp.calendar_quarter,
    dp.fiscal_year,
    dp.fiscal_quarter,
    f.provider_id,
    sum(f.spend_amount)::numeric(19, 4)          as spend_amount,
    (sum(f.spend_amount) / 1000000.0)::numeric(19, 6) as spend_millions
from {{ ref('fct_service_spend') }} f
join {{ ref('dim_period') }} dp on dp.period_key = f.period_key
group by
    dp.calendar_year,
    dp.calendar_quarter,
    dp.fiscal_year,
    dp.fiscal_quarter,
    f.provider_id
