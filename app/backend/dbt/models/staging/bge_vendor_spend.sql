{{ config(materialized='materialized_view') }}

select
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    vendor,
    organization_name,
    sum(spend_amount)::numeric(19, 4) as spend_amount,
    (sum(spend_amount) / 1000000.0)::numeric(19, 6) as spend_millions
from {{ ref('stg_service_spend_line_items') }}
where organization_name is not null
group by
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    vendor,
    organization_name
