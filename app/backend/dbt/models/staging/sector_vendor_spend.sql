{{ config(materialized='materialized_view') }}

select
    li.calendar_year,
    li.calendar_quarter,
    li.fiscal_year,
    li.fiscal_quarter,
    li.vendor,
    s.name as sector,
    sum(li.spend_amount)::numeric(19, 4)          as spend_amount,
    (sum(li.spend_amount) / 1000000.0)::numeric(19, 6) as spend_millions
from {{ ref('int_service_spend_line_items') }} li
join {{ source('reference_data', 'sector') }} s on s.id = li.sector_id
group by
    li.calendar_year,
    li.calendar_quarter,
    li.fiscal_year,
    li.fiscal_quarter,
    li.vendor,
    s.name
