-- Built from the distinct periods present in the spend line items, joined to the
-- fiscal_calendar seed for the calendar-month -> quarter/fiscal mapping.
-- Reads fct_service_spend (a table) rather than the int_service_spend_line_items
-- view, so the heavy spend query runs once per dbt run instead of twice in parallel.
with periods as (
    select distinct period_key
    from {{ ref('fct_service_spend') }}
    where period_key is not null
)
select
    p.period_key,
    extract(year from p.period_key)::integer                       as calendar_year,
    fc.calendar_quarter,
    extract(year from p.period_key)::integer + fc.fiscal_year_offset as fiscal_year,
    fc.fiscal_quarter
from periods p
left join {{ ref('fiscal_calendar') }} fc
    on fc.calendar_month = extract(month from p.period_key)::integer
