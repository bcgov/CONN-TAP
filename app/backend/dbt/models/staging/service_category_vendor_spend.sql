{{ config(materialized='materialized_view') }}

select
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    service_category,
    vendor,
    sum(spend_amount)::numeric(19, 4) as spend_amount,
    (sum(spend_amount) / 1000000.0)::numeric(19, 6) as spend_millions
from {{ ref('int_service_spend_line_items') }}
group by
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    service_category,
    vendor
