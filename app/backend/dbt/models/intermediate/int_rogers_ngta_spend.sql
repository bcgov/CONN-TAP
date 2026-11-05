{{ config(materialized='view') }}

-- Rogers NGTA spend normalized to the shared line-item shape, so
-- int_service_spend_line_items stays vendor-agnostic.

with rogers as (
    select * from {{ ref('stg_rogers_spend') }}
),

pricebook as (
    select * from {{ ref('stg_rogers_pricebook_services') }}
)

select
    r.vendor,
    r.source_system,
    r.source_table,
    r.raw_id,
    r.month_start,
    -- TO wants school districts grouped together separately, for example: under ECC.
    -- organization_name / sub_organization_name are already alias-resolved in
    -- stg_rogers_spend, so the sub-org check below sees 'School District 71'
    -- rather than the raw 'DISTRICT 71 COMOX VALLEY'.
    case
        when lower(r.organization_name) like '%school district%'
            or lower(r.sub_organization_name) like '%school district%'
            then 'School Districts'
        else r.organization_name
    end as organization_name,
    r.sub_organization_name,
    coalesce(pb.service_category_code, r.source_service_family) as lookup_code,
    r.spend_amount
from rogers r
left join pricebook pb on pb.service_id_key = r.source_service_id
