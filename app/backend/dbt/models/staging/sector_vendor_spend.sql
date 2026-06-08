{{ config(materialized='materialized_view') }}

select
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    vendor,
    case
        when organization_name in ('FHA', 'FNHA', 'IHA', 'NHA', 'PHSA', 'VCHA (+PHC)', 'VIHA')
          or lower(organization_name) like '%health author%'
            then 'Health Authorities'
        when organization_name in ('BC Hydro', 'BCLC', 'WSBC', 'ICBC')
            then 'Crown Corporations'
        when organization_name = 'School Districts'
          or lower(organization_name) like '%school district%'
            then 'School Districts'
        when organization_name = 'ECC'
            then 'Gov & ECC'
        else 'Gov & ECC'
    end as sector,
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
    sector
