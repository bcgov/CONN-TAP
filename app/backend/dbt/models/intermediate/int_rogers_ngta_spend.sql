{{ config(materialized='view') }}

-- Rogers NGTA spend normalized to the shared line-item shape, so
-- int_service_spend_line_items stays vendor-agnostic.

with rogers as (
    select * from {{ ref('stg_rogers_spend') }}
)

select
    vendor,
    source_system,
    source_table,
    raw_id,
    month_start,
    -- TO wants school districts grouped together separately, for example: under ECC.
    -- organization_name / sub_organization_name are already alias-resolved in
    -- stg_rogers_spend, so the sub-org check below sees 'School District 71'
    -- rather than the raw 'DISTRICT 71 COMOX VALLEY'.
    case
        when lower(organization_name) like '%school district%'
            or lower(sub_organization_name) like '%school district%'
            then 'School Districts'
        else organization_name
    end as organization_name,
    sub_organization_name,
    source_service_family as lookup_code,
    spend_amount
from rogers
