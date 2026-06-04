{{ config(materialized='materialized_view') }}

select
    calendar_year,
    calendar_quarter,
    fiscal_year,
    fiscal_quarter,
    vendor,
    case
        -- Health Authorities
        when organization_name in (
            'Fraser Health Authority',
            'FRASER HEALTH AUTHORITY',
            'Fraser Health',
            'FHA',
            'First Nations Health Authority',
            'FIRST NATIONS HEALTH AUTHORITY',
            'FNHA',
            'Interior Health Authority',
            'IHA',
            'Northern Health Authority',
            'NHA',
            'Provincial Health Services Authority',
            'PROVINCIAL HEALTH SERVICES AUTHORITY',
            'PHSA',
            'Vancouver Coastal Health Authority',
            'VCHA',
            'Vancouver Island Health Authority',
            'VANCOUVER ISLAND HEALTH AUTHORITY',
            'VIHA',
            'Providence Health Care',
            'PROVIDENCE HEALTH CARE',
            'CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY'
        )
          or lower(organization_name) like '%health author%'
          or lower(organization_name) like '%health serv%'
            then 'Health Authorities'

        -- Crown Corporations
        when organization_name in (
            'BC Hydro',
            'BC HYDRO',
            'BCH',
            'BRITISH COLUMBIA HYDRO & POWER AUTHORITY',
            'British Columbia Lottery Corporation',
            'BCLC',
            'BC LOTTERY',
            'WorkSafe BC',
            'Worksafe BC',
            'WSBC',
            'WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA',
            'Insurance Corporation of BC',
            'INSURANCE CORPORATION OF BRITISH COLUMB.',
            'INSURANCE CORPORATION OF BRITISH COLUMBIA - ICBC',
            'ICBC',
            'BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH',
            'GBC - LIQUOR DISTRIBUTION BRANCH'
        )
          or lower(organization_name) like '%bc hydro%'
          or lower(organization_name) like '%workers compensation%'
          or lower(organization_name) like '%worksafe%'
          or lower(organization_name) like '%insurance corporation%'
          or lower(organization_name) like '%liquor distribution%'
            then 'Crown Corporations'

        -- School Districts
        when organization_name in (
            'School Districts',
            'TSMA LITE SCHOOL DISTRICTS',
            'SCHLDIST',
            'SD'
        )
          or lower(organization_name) like '%school district%'
            then 'School Districts'

        -- Gov & ECC: BC Gov, all BC Min *, ministries, and everything else
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
